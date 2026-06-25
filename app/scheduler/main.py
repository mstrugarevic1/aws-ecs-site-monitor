import asyncio

from app.common.logging import configure_logging
from app.runtime import queue, repository
from app.services.scheduler import SchedulerService


async def run() -> int:
    configure_logging()
    return await SchedulerService(repository, queue).enqueue_enabled_monitors()


if __name__ == "__main__":
    asyncio.run(run())
