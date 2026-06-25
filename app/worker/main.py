import asyncio
import signal

from app.common.logging import configure_logging
from app.runtime import notifier, queue, repository
from app.services.http_checker import HttpChecker
from app.services.worker import WorkerService


async def run_once() -> bool:
    configure_logging()
    return await WorkerService(repository, queue, HttpChecker(), notifier).process_next()


async def run_forever() -> None:
    configure_logging()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    worker = WorkerService(repository, queue, HttpChecker(), notifier)
    while not stop.is_set():
        processed = await worker.process_next()
        if not processed:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_forever())
