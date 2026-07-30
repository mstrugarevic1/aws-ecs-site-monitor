import uvicorn
from fastapi import FastAPI

from app import runtime
from app.api.routes import router
from app.common.logging import configure_logging
from app.repositories.interfaces import MonitorRepository
from app.services.notifier import NotificationPublisher
from app.services.queue import QueueClient


def create_app(
    repository: MonitorRepository | None = None,
    queue: QueueClient | None = None,
    notifier: NotificationPublisher | None = None,
) -> FastAPI:
    configure_logging()
    app = FastAPI(title="AWS ECS Internal Service Monitor", version="0.1.0")
    app.state.repository = repository if repository is not None else runtime.repository
    app.state.queue = queue if queue is not None else runtime.queue
    app.state.notifier = notifier if notifier is not None else runtime.notifier
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000)
