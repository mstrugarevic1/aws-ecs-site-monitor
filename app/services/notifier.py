import logging
from typing import Protocol

from app.domain.models import Monitor


class NotificationPublisher(Protocol):
    async def alert(self, monitor: Monitor) -> None: ...
    async def recovery(self, monitor: Monitor) -> None: ...


class LocalLoggingNotifier:
    def __init__(self) -> None:
        self.notifications: list[tuple[str, str]] = []
        self._logger = logging.getLogger(__name__)

    async def alert(self, monitor: Monitor) -> None:
        self.notifications.append(("alert", monitor.monitor_id))
        self._logger.warning(
            "monitor alert threshold crossed",
            extra={"component": "worker", "monitor_id": monitor.monitor_id, "status": monitor.status},
        )

    async def recovery(self, monitor: Monitor) -> None:
        self.notifications.append(("recovery", monitor.monitor_id))
        self._logger.info(
            "monitor recovered",
            extra={"component": "worker", "monitor_id": monitor.monitor_id, "status": monitor.status},
        )
