import pytest

from app.domain.models import CheckJob, Monitor, MonitorStatus
from app.repositories.memory import InMemoryMonitorRepository
from app.services.http_checker import HttpCheckOutcome
from app.services.notifier import LocalLoggingNotifier
from app.services.queue import InMemoryQueueClient
from app.services.scheduler import SchedulerService
from app.services.worker import WorkerService


class StaticChecker:
    def __init__(self, *outcomes: HttpCheckOutcome) -> None:
        self.outcomes = list(outcomes)

    async def check(self, url: str, timeout_seconds: int) -> HttpCheckOutcome:
        return self.outcomes.pop(0)


class CrashingChecker:
    async def check(self, url: str, timeout_seconds: int) -> HttpCheckOutcome:
        raise RuntimeError("checker crashed")


async def create_monitor(repository: InMemoryMonitorRepository, *, failure_threshold: int = 3) -> Monitor:
    return await repository.create(
        Monitor(
            name="Example",
            url="https://example.com/health",
            expected_status=200,
            timeout_seconds=5,
            failure_threshold=failure_threshold,
        )
    )


async def test_scheduler_job_creation_only_for_enabled_monitors() -> None:
    repository = InMemoryMonitorRepository()
    enabled = await create_monitor(repository)
    disabled = await create_monitor(repository)
    await repository.update(disabled.monitor_id, {"enabled": False})
    queue = InMemoryQueueClient()

    count = await SchedulerService(repository, queue).enqueue_enabled_monitors()
    message = await queue.receive_one()

    assert count == 1
    assert message is not None
    assert message.job.monitor_id == enabled.monitor_id


async def test_queue_message_parsing() -> None:
    job = CheckJob.model_validate_json('{"job_id":"job-1","monitor_id":"monitor-1"}')

    assert job.job_id == "job-1"
    assert job.monitor_id == "monitor-1"


async def test_worker_success_resets_failure_counter() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await create_monitor(repository)
    await repository.update(
        monitor.monitor_id,
        {"status": MonitorStatus.down, "consecutive_failures": 2},
    )
    queue = InMemoryQueueClient()
    await queue.send_check_job(CheckJob(job_id="job-1", monitor_id=monitor.monitor_id))
    notifier = LocalLoggingNotifier()

    processed = await WorkerService(
        repository,
        queue,
        StaticChecker(HttpCheckOutcome(http_status=200, latency_ms=20)),
        notifier,
    ).process_next()

    updated = await repository.get(monitor.monitor_id)
    assert processed is True
    assert updated is not None
    assert updated.status == MonitorStatus.up
    assert updated.consecutive_failures == 0
    assert updated.last_success_at is not None
    assert notifier.notifications == [("recovery", monitor.monitor_id)]


async def test_worker_unexpected_status_increments_failures_and_alerts_once() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await create_monitor(repository, failure_threshold=3)
    await repository.update(monitor.monitor_id, {"consecutive_failures": 2})
    queue = InMemoryQueueClient()
    await queue.send_check_job(CheckJob(job_id="job-1", monitor_id=monitor.monitor_id))
    await queue.send_check_job(CheckJob(job_id="job-2", monitor_id=monitor.monitor_id))
    notifier = LocalLoggingNotifier()
    worker = WorkerService(
        repository,
        queue,
        StaticChecker(
            HttpCheckOutcome(http_status=500, latency_ms=12),
            HttpCheckOutcome(http_status=500, latency_ms=13),
        ),
        notifier,
    )

    assert await worker.process_next() is True
    assert await worker.process_next() is True

    updated = await repository.get(monitor.monitor_id)
    assert updated is not None
    assert updated.status == MonitorStatus.down
    assert updated.consecutive_failures == 4
    assert notifier.notifications == [("alert", monitor.monitor_id)]


async def test_worker_timeout_records_down_result() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await create_monitor(repository)
    queue = InMemoryQueueClient()
    await queue.send_check_job(CheckJob(job_id="job-1", monitor_id=monitor.monitor_id))

    await WorkerService(
        repository,
        queue,
        StaticChecker(HttpCheckOutcome(None, None, "timeout", "too slow")),
        LocalLoggingNotifier(),
    ).process_next()

    results = await repository.list_results(monitor.monitor_id)
    assert results[0].status == MonitorStatus.down
    assert results[0].error_type == "timeout"


async def test_worker_idempotent_job_processing() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await create_monitor(repository)
    queue = InMemoryQueueClient()
    await queue.send_check_job(CheckJob(job_id="same-job", monitor_id=monitor.monitor_id))
    await queue.send_check_job(CheckJob(job_id="same-job", monitor_id=monitor.monitor_id))
    worker = WorkerService(
        repository,
        queue,
        StaticChecker(
            HttpCheckOutcome(http_status=500, latency_ms=1),
            HttpCheckOutcome(http_status=500, latency_ms=1),
        ),
        LocalLoggingNotifier(),
    )

    assert await worker.process_next() is True
    assert await worker.process_next() is True

    assert len(await repository.list_results(monitor.monitor_id)) == 1
    updated = await repository.get(monitor.monitor_id)
    assert updated is not None
    assert updated.consecutive_failures == 1


async def test_queue_retries_failed_message_then_moves_to_dead_letters() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await create_monitor(repository)
    queue = InMemoryQueueClient(max_receive_count=2)
    await queue.send_check_job(CheckJob(job_id="job-1", monitor_id=monitor.monitor_id))
    worker = WorkerService(repository, queue, CrashingChecker(), LocalLoggingNotifier())

    with pytest.raises(RuntimeError):
        await worker.process_next()
    with pytest.raises(RuntimeError):
        await worker.process_next()

    assert await queue.receive_one() is None
    assert len(queue.dead_letters) == 1
    assert queue.dead_letters[0].job.job_id == "job-1"
