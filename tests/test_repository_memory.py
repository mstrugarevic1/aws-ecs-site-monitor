from datetime import UTC, datetime

from app.domain.models import CheckResult, Monitor, MonitorStatus
from app.repositories.memory import InMemoryMonitorRepository


async def test_memory_repository_crud_and_results() -> None:
    repository = InMemoryMonitorRepository()
    monitor = await repository.create(
        Monitor(
            name="Example",
            url="https://example.com/health",
            expected_status=200,
            timeout_seconds=5,
            failure_threshold=3,
        )
    )

    assert await repository.get(monitor.monitor_id) == monitor

    updated = await repository.update(monitor.monitor_id, {"enabled": False})
    assert updated is not None
    assert updated.enabled is False

    result = CheckResult(
        monitor_id=monitor.monitor_id,
        checked_at=datetime.now(UTC),
        job_id="job-1",
        status=MonitorStatus.up,
        http_status=200,
        latency_ms=12,
    )
    await repository.add_result(result)
    await repository.add_result(result)

    assert len(await repository.list_results(monitor.monitor_id)) == 1
    assert await repository.delete(monitor.monitor_id) is True
    assert await repository.get(monitor.monitor_id) is None
