from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class MonitorStatus(StrEnum):
    unknown = "UNKNOWN"
    up = "UP"
    down = "DOWN"


class Monitor(BaseModel):
    monitor_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=100)
    url: str
    expected_status: int = Field(ge=100, le=599)
    timeout_seconds: int = Field(ge=1, le=30)
    failure_threshold: int = Field(ge=1, le=10)
    enabled: bool = True
    status: MonitorStatus = MonitorStatus.unknown
    latency_ms: int | None = None
    consecutive_failures: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None


class CheckResult(BaseModel):
    monitor_id: str
    checked_at: datetime
    job_id: str
    status: MonitorStatus
    http_status: int | None = None
    latency_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None


class CheckJob(BaseModel):
    job_id: str
    monitor_id: str
