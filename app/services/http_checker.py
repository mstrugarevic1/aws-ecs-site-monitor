import time
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class HttpCheckOutcome:
    http_status: int | None
    latency_ms: int | None
    error_type: str | None = None
    error_message: str | None = None


class CheckClient(Protocol):
    async def check(self, url: str, timeout_seconds: int) -> HttpCheckOutcome: ...


class HttpChecker:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    async def check(self, url: str, timeout_seconds: int) -> HttpCheckOutcome:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                follow_redirects=False,
                timeout=timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.get(url)
            return HttpCheckOutcome(
                http_status=response.status_code,
                latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
            )
        except httpx.TimeoutException as exc:
            return HttpCheckOutcome(None, None, "timeout", _bounded(str(exc) or "request timed out"))
        except httpx.RequestError as exc:
            return HttpCheckOutcome(None, None, exc.__class__.__name__, _bounded(str(exc)))


def safe_host(url: str) -> str:
    return urlparse(url).hostname or "unknown"


def _bounded(value: str, limit: int = 200) -> str:
    return value[:limit]
