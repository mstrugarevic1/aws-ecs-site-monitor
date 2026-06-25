from collections import deque
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.domain.models import CheckJob


@dataclass(frozen=True)
class QueueMessage:
    receipt_handle: str
    job: CheckJob
    receive_count: int = 1


class QueueClient(Protocol):
    async def send_check_job(self, job: CheckJob) -> None: ...
    async def receive_one(self) -> QueueMessage | None: ...
    async def delete(self, receipt_handle: str) -> None: ...
    async def release(self, receipt_handle: str) -> None: ...


class InMemoryQueueClient:
    def __init__(self, max_receive_count: int = 3) -> None:
        self.max_receive_count = max_receive_count
        self._available: deque[QueueMessage] = deque()
        self._inflight: dict[str, QueueMessage] = {}
        self.dead_letters: list[QueueMessage] = []

    async def send_check_job(self, job: CheckJob) -> None:
        self._available.append(QueueMessage(receipt_handle=str(uuid4()), job=job))

    async def receive_one(self) -> QueueMessage | None:
        if not self._available:
            return None
        message = self._available.popleft()
        self._inflight[message.receipt_handle] = message
        return message

    async def delete(self, receipt_handle: str) -> None:
        self._inflight.pop(receipt_handle, None)

    async def release(self, receipt_handle: str) -> None:
        message = self._inflight.pop(receipt_handle, None)
        if message is None:
            return
        if message.receive_count >= self.max_receive_count:
            self.dead_letters.append(message)
            return
        self._available.append(
            QueueMessage(
                receipt_handle=str(uuid4()),
                job=message.job,
                receive_count=message.receive_count + 1,
            )
        )
