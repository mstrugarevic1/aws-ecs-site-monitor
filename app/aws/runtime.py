import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.domain.models import CheckJob, CheckResult, Monitor
from app.services.queue import QueueMessage


def _clean(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None}


class DynamoDBMonitorRepository:
    def __init__(self, monitors_table: str, results_table: str, region_name: str, result_ttl_days: int = 30) -> None:
        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.monitors = dynamodb.Table(monitors_table)
        self.results = dynamodb.Table(results_table)
        self.result_ttl_days = result_ttl_days

    async def create(self, monitor: Monitor) -> Monitor:
        await asyncio.to_thread(self.monitors.put_item, Item=_clean(monitor.model_dump(mode="json")))
        return monitor

    async def list_monitors(self) -> list[Monitor]:
        response = await asyncio.to_thread(self.monitors.scan)
        return [Monitor.model_validate(item) for item in response.get("Items", [])]

    async def get(self, monitor_id: str) -> Monitor | None:
        response = await asyncio.to_thread(self.monitors.get_item, Key={"monitor_id": monitor_id})
        item = response.get("Item")
        return Monitor.model_validate(item) if item else None

    async def update(self, monitor_id: str, changes: dict) -> Monitor | None:
        current = await self.get(monitor_id)
        if current is None:
            return None
        data = current.model_dump()
        data.update(changes)
        data["updated_at"] = datetime.now(UTC)
        updated = Monitor(**data)
        await asyncio.to_thread(self.monitors.put_item, Item=_clean(updated.model_dump(mode="json")))
        return updated

    async def delete(self, monitor_id: str) -> bool:
        existed = await self.get(monitor_id) is not None
        await asyncio.to_thread(self.monitors.delete_item, Key={"monitor_id": monitor_id})
        for result in await self.list_results(monitor_id):
            checked_at = result.checked_at.isoformat().replace("+00:00", "Z")
            await asyncio.to_thread(self.results.delete_item, Key={"monitor_id": monitor_id, "checked_at": checked_at})
        return existed

    async def add_result(self, result: CheckResult) -> CheckResult:
        if await self.result_exists(result.monitor_id, result.job_id):
            return result
        item = _clean(result.model_dump(mode="json"))
        item["expires_at"] = int((datetime.now(UTC) + timedelta(days=self.result_ttl_days)).timestamp())
        await asyncio.to_thread(self.results.put_item, Item=item)
        return result

    async def result_exists(self, monitor_id: str, job_id: str) -> bool:
        return any(result.job_id == job_id for result in await self.list_results(monitor_id))

    async def list_results(self, monitor_id: str) -> list[CheckResult]:
        response = await asyncio.to_thread(
            self.results.query,
            KeyConditionExpression=Key("monitor_id").eq(monitor_id),
            ScanIndexForward=False,
        )
        return [CheckResult.model_validate(item) for item in response.get("Items", [])]

    async def ready(self) -> bool:
        try:
            await asyncio.to_thread(self.monitors.load)
            await asyncio.to_thread(self.results.load)
        except Exception:
            return False
        return True


class SQSQueueClient:
    def __init__(self, queue_url: str, region_name: str) -> None:
        self.queue_url = queue_url
        self.client = boto3.client("sqs", region_name=region_name)

    async def send_check_job(self, job: CheckJob) -> None:
        await asyncio.to_thread(self.client.send_message, QueueUrl=self.queue_url, MessageBody=job.model_dump_json())

    async def receive_one(self) -> QueueMessage | None:
        response = await asyncio.to_thread(
            self.client.receive_message,
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=1,
            AttributeNames=["ApproximateReceiveCount"],
        )
        messages = response.get("Messages", [])
        if not messages:
            return None
        message = messages[0]
        return QueueMessage(
            receipt_handle=message["ReceiptHandle"],
            job=CheckJob.model_validate_json(message["Body"]),
            receive_count=int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1")),
        )

    async def delete(self, receipt_handle: str) -> None:
        await asyncio.to_thread(self.client.delete_message, QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)

    async def release(self, receipt_handle: str) -> None:
        await asyncio.to_thread(
            self.client.change_message_visibility,
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=0,
        )


class SNSNotifier:
    def __init__(self, topic_arn: str, region_name: str) -> None:
        self.topic_arn = topic_arn
        self.client = boto3.client("sns", region_name=region_name)

    async def alert(self, monitor: Monitor) -> None:
        await self._publish("alert", monitor)

    async def recovery(self, monitor: Monitor) -> None:
        await self._publish("recovery", monitor)

    async def _publish(self, event_type: str, monitor: Monitor) -> None:
        await asyncio.to_thread(
            self.client.publish,
            TopicArn=self.topic_arn,
            Subject=f"Monitor {event_type}: {monitor.name}",
            Message=json.dumps({"event": event_type, "monitor": monitor.model_dump(mode="json")}),
        )
