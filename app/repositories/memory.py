from copy import deepcopy
from datetime import UTC, datetime

from app.domain.models import CheckResult, Monitor


class InMemoryMonitorRepository:
    def __init__(self) -> None:
        self._monitors: dict[str, Monitor] = {}
        self._results: dict[str, list[CheckResult]] = {}

    async def create(self, monitor: Monitor) -> Monitor:
        self._monitors[monitor.monitor_id] = deepcopy(monitor)
        return deepcopy(monitor)

    async def list_monitors(self) -> list[Monitor]:
        return [deepcopy(item) for item in self._monitors.values()]

    async def get(self, monitor_id: str) -> Monitor | None:
        monitor = self._monitors.get(monitor_id)
        return deepcopy(monitor) if monitor else None

    async def update(self, monitor_id: str, changes: dict) -> Monitor | None:
        current = self._monitors.get(monitor_id)
        if current is None:
            return None
        data = current.model_dump()
        data.update(changes)
        data["updated_at"] = datetime.now(UTC)
        updated = Monitor(**data)
        self._monitors[monitor_id] = updated
        return deepcopy(updated)

    async def delete(self, monitor_id: str) -> bool:
        existed = monitor_id in self._monitors
        self._monitors.pop(monitor_id, None)
        self._results.pop(monitor_id, None)
        return existed

    async def add_result(self, result: CheckResult) -> CheckResult:
        results = self._results.setdefault(result.monitor_id, [])
        if not any(existing.job_id == result.job_id for existing in results):
            results.append(deepcopy(result))
            results.sort(key=lambda item: item.checked_at, reverse=True)
        return deepcopy(result)

    async def result_exists(self, monitor_id: str, job_id: str) -> bool:
        return any(result.job_id == job_id for result in self._results.get(monitor_id, []))

    async def list_results(self, monitor_id: str) -> list[CheckResult]:
        return [deepcopy(item) for item in self._results.get(monitor_id, [])]

    async def ready(self) -> bool:
        return True
