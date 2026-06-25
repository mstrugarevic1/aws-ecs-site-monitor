import logging
from uuid import uuid4

from app.domain.models import CheckJob
from app.repositories.interfaces import MonitorRepository
from app.services.http_checker import safe_host
from app.services.queue import QueueClient


class SchedulerService:
    def __init__(self, repository: MonitorRepository, queue: QueueClient) -> None:
        self.repository = repository
        self.queue = queue
        self.logger = logging.getLogger(__name__)

    async def enqueue_enabled_monitors(self) -> int:
        count = 0
        for monitor in await self.repository.list_monitors():
            if not monitor.enabled:
                continue
            job = CheckJob(job_id=str(uuid4()), monitor_id=monitor.monitor_id)
            await self.queue.send_check_job(job)
            count += 1
            self.logger.info(
                "check job enqueued",
                extra={
                    "component": "scheduler",
                    "monitor_id": monitor.monitor_id,
                    "job_id": job.job_id,
                    "target_host": safe_host(monitor.url),
                },
            )
        self.logger.info("scheduler completed", extra={"component": "scheduler", "status": "ok", "latency_ms": count})
        return count
