import uvicorn
from fastapi import FastAPI

from app.api.routes import router
from app.common.logging import configure_logging
from app.repositories.memory import InMemoryMonitorRepository
from app.services.notifier import LocalLoggingNotifier
from app.services.queue import InMemoryQueueClient


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="AWS ECS Internal Service Monitor", version="0.1.0")
    app.state.repository = InMemoryMonitorRepository()
    app.state.queue = InMemoryQueueClient()
    app.state.notifier = LocalLoggingNotifier()
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000)
