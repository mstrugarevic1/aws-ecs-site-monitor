from app.repositories.memory import InMemoryMonitorRepository
from app.services.notifier import LocalLoggingNotifier
from app.services.queue import InMemoryQueueClient

repository = InMemoryMonitorRepository()
queue = InMemoryQueueClient()
notifier = LocalLoggingNotifier()
