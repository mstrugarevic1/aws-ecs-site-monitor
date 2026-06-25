from datetime import UTC, datetime

from app.domain.models import CheckResult, Monitor, MonitorStatus
from app.repositories.interfaces import MonitorRepository
from app.services.http_checker import CheckClient
from app.services.notifier import NotificationPublisher
from app.services.queue import QueueClient, QueueMessage


class WorkerService:
    def __init__(
        self,
        repository: MonitorRepository,
        queue: QueueClient,
        checker: CheckClient,
        notifier: NotificationPublisher,
    ) -> None:
        self.repository = repository
        self.queue = queue
        self.checker = checker
        self.notifier = notifier

    async def process_next(self) -> bool:
        message = await self.queue.receive_one()
        if message is None:
            return False
        try:
            permanent = await self._process(message)
        except Exception:
            await self.queue.release(message.receipt_handle)
            raise
        if permanent:
            await self.queue.delete(message.receipt_handle)
        return True

    async def _process(self, message: QueueMessage) -> bool:
        job = message.job
        monitor = await self.repository.get(job.monitor_id)
        if monitor is None or not monitor.enabled:
            return True
        if await self.repository.result_exists(job.monitor_id, job.job_id):
            return True

        outcome = await self.checker.check(monitor.url, monitor.timeout_seconds)
        status = MonitorStatus.up if outcome.http_status == monitor.expected_status else MonitorStatus.down
        now = datetime.now(UTC)
        result = CheckResult(
            monitor_id=monitor.monitor_id,
            checked_at=now,
            job_id=job.job_id,
            status=status,
            http_status=outcome.http_status,
            latency_ms=outcome.latency_ms,
            error_type=outcome.error_type,
            error_message=outcome.error_message,
        )
        await self.repository.add_result(result)
        updated = await self._update_monitor(monitor, result, now)
        await self._notify(monitor, updated)
        return True

    async def _update_monitor(self, monitor: Monitor, result: CheckResult, checked_at: datetime) -> Monitor:
        failures = 0 if result.status == MonitorStatus.up else monitor.consecutive_failures + 1
        changes = {
            "status": result.status,
            "latency_ms": result.latency_ms,
            "consecutive_failures": failures,
            "last_checked_at": checked_at,
            "last_success_at": checked_at if result.status == MonitorStatus.up else monitor.last_success_at,
        }
        updated = await self.repository.update(monitor.monitor_id, changes)
        if updated is None:
            raise RuntimeError("monitor disappeared during update")
        return updated

    async def _notify(self, before: Monitor, after: Monitor) -> None:
        if before.consecutive_failures < before.failure_threshold <= after.consecutive_failures:
            await self.notifier.alert(after)
        if before.status == MonitorStatus.down and after.status == MonitorStatus.up:
            await self.notifier.recovery(after)
