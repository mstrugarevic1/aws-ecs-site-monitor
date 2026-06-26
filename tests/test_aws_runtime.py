import importlib
import json
import sys
import types
from typing import Any, cast

from app.common.config import Settings
from app.domain.models import CheckJob, Monitor


class FakeAWSClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.messages: list[dict] = []

    def send_message(self, **kwargs) -> None:
        self.calls.append(("send_message", kwargs))

    def receive_message(self, **kwargs) -> dict:
        self.calls.append(("receive_message", kwargs))
        return {"Messages": self.messages}

    def delete_message(self, **kwargs) -> None:
        self.calls.append(("delete_message", kwargs))

    def change_message_visibility(self, **kwargs) -> None:
        self.calls.append(("change_message_visibility", kwargs))

    def publish(self, **kwargs) -> None:
        self.calls.append(("publish", kwargs))


def import_aws_runtime(fake_client: FakeAWSClient):
    boto3 = types.ModuleType("boto3")

    def client(*args: object, **kwargs: object) -> FakeAWSClient:
        return fake_client

    def resource(*args: object, **kwargs: object) -> None:
        return None

    cast(Any, boto3).client = client
    cast(Any, boto3).resource = resource
    dynamodb = types.ModuleType("boto3.dynamodb")
    conditions = types.ModuleType("boto3.dynamodb.conditions")

    def key(name: str) -> types.SimpleNamespace:
        return types.SimpleNamespace(eq=lambda value: (name, value))

    cast(Any, conditions).Key = key
    sys.modules["boto3"] = boto3
    sys.modules["boto3.dynamodb"] = dynamodb
    sys.modules["boto3.dynamodb.conditions"] = conditions
    sys.modules.pop("app.aws.runtime", None)
    return importlib.import_module("app.aws.runtime")


def test_settings_enable_aws_runtime_only_when_all_values_exist() -> None:
    assert not Settings().aws_runtime_enabled
    assert Settings(
        AWS_REGION="us-east-1",
        MONITORS_TABLE="monitors",
        CHECK_RESULTS_TABLE="results",
        QUEUE_URL="https://sqs.example/queue",
        ALERTS_TOPIC_ARN="arn:aws:sns:us-east-1:123:alerts",
    ).aws_runtime_enabled


async def test_sqs_queue_client_maps_jobs_and_receipts() -> None:
    fake = FakeAWSClient()
    runtime = import_aws_runtime(fake)
    client = runtime.SQSQueueClient("queue-url", "us-east-1")
    job = CheckJob(job_id="job-1", monitor_id="monitor-1")

    await client.send_check_job(job)
    fake.messages.append(
        {
            "ReceiptHandle": "receipt-1",
            "Body": job.model_dump_json(),
            "Attributes": {"ApproximateReceiveCount": "2"},
        }
    )
    message = await client.receive_one()
    await client.delete("receipt-1")
    await client.release("receipt-2")

    assert json.loads(fake.calls[0][1]["MessageBody"]) == {"job_id": "job-1", "monitor_id": "monitor-1"}
    assert message is not None
    assert message.receipt_handle == "receipt-1"
    assert message.receive_count == 2
    assert fake.calls[-2] == ("delete_message", {"QueueUrl": "queue-url", "ReceiptHandle": "receipt-1"})
    assert fake.calls[-1][1]["VisibilityTimeout"] == 0


async def test_sns_notifier_publishes_monitor_event() -> None:
    fake = FakeAWSClient()
    runtime = import_aws_runtime(fake)
    notifier = runtime.SNSNotifier("topic-arn", "us-east-1")

    await notifier.alert(
        Monitor(
            monitor_id="monitor-1",
            name="Example",
            url="https://example.com/health",
            expected_status=200,
            timeout_seconds=5,
            failure_threshold=3,
        )
    )

    assert fake.calls[0][0] == "publish"
    assert fake.calls[0][1]["TopicArn"] == "topic-arn"
    assert json.loads(fake.calls[0][1]["Message"])["event"] == "alert"
