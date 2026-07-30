from pydantic import BaseModel, Field, field_validator

from app.domain.models import MonitorStatus
from app.domain.validation import validate_target_url


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str
    expected_status: int = Field(default=200, ge=100, le=599)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    failure_threshold: int = Field(default=3, ge=1, le=10)
    enabled: bool = True

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        return validate_target_url(value)


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = None
    expected_status: int | None = Field(default=None, ge=100, le=599)
    timeout_seconds: int | None = Field(default=None, ge=1, le=30)
    failure_threshold: int | None = Field(default=None, ge=1, le=10)
    enabled: bool | None = None

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return validate_target_url(value) if value is not None else value


class MonitorResponse(MonitorCreate):
    monitor_id: str
    status: MonitorStatus
    latency_ms: int | None
    consecutive_failures: int
    created_at: str
    updated_at: str
    last_checked_at: str | None
    last_success_at: str | None


class ManualCheckResponse(BaseModel):
    job_id: str
    monitor_id: str
    status: str = "accepted"
    note: str = "Check job queued."
