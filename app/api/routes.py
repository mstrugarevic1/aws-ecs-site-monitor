from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.schemas import ManualCheckResponse, MonitorCreate, MonitorUpdate
from app.common.config import settings
from app.domain.models import CheckJob, Monitor
from app.repositories.interfaces import MonitorRepository
from app.services.http_checker import CheckClient
from app.services.notifier import NotificationPublisher
from app.services.queue import InMemoryQueueClient, QueueClient
from app.services.worker import WorkerService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_repository(request: Request) -> MonitorRepository:
    return request.app.state.repository


def get_queue(request: Request) -> QueueClient:
    return request.app.state.queue


def get_notifier(request: Request) -> NotificationPublisher:
    return request.app.state.notifier


def get_checker(request: Request) -> CheckClient:
    return request.app.state.checker


RepositoryDep = Annotated[MonitorRepository, Depends(get_repository)]
QueueDep = Annotated[QueueClient, Depends(get_queue)]
NotifierDep = Annotated[NotificationPublisher, Depends(get_notifier)]
CheckerDep = Annotated[CheckClient, Depends(get_checker)]


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, repository: RepositoryDep):
    monitors = await repository.list_monitors()
    return templates.TemplateResponse(request, "dashboard.html", {"monitors": monitors})


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(repository: RepositoryDep) -> dict[str, str]:
    if not await repository.ready():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="repository not ready")
    return {"status": "ready"}


@router.get("/version")
async def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version}


@router.post("/api/v1/monitors", response_model=Monitor, status_code=status.HTTP_201_CREATED)
async def create_monitor(payload: MonitorCreate, repository: RepositoryDep):
    return await repository.create(Monitor(**payload.model_dump()))


@router.get("/api/v1/monitors", response_model=list[Monitor])
async def list_monitors(repository: RepositoryDep):
    return await repository.list_monitors()


@router.get("/api/v1/monitors/{monitor_id}", response_model=Monitor)
async def get_monitor(monitor_id: str, repository: RepositoryDep):
    monitor = await repository.get(monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="monitor not found")
    return monitor


@router.patch("/api/v1/monitors/{monitor_id}", response_model=Monitor)
async def update_monitor(
    monitor_id: str,
    payload: MonitorUpdate,
    repository: RepositoryDep,
):
    changes = payload.model_dump(exclude_unset=True)
    monitor = await repository.update(monitor_id, changes)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="monitor not found")
    return monitor


@router.delete("/api/v1/monitors/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(monitor_id: str, repository: RepositoryDep):
    if not await repository.delete(monitor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="monitor not found")


@router.post(
    "/api/v1/monitors/{monitor_id}/check",
    response_model=ManualCheckResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_manual_check(
    monitor_id: str,
    repository: RepositoryDep,
    queue: QueueDep,
    notifier: NotifierDep,
    checker: CheckerDep,
):
    monitor = await repository.get(monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="monitor not found")
    job_id = str(uuid4())
    await queue.send_check_job(CheckJob(job_id=job_id, monitor_id=monitor_id))
    note = "Check job queued."
    if isinstance(queue, InMemoryQueueClient):
        await WorkerService(repository, queue, checker, notifier).process_next()
        note = "Check job processed."
    return ManualCheckResponse(job_id=job_id, monitor_id=monitor_id, note=note)


@router.get("/api/v1/monitors/{monitor_id}/results")
async def list_results(monitor_id: str, repository: RepositoryDep):
    if await repository.get(monitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="monitor not found")
    return await repository.list_results(monitor_id)
