from app.common.config import settings
from app.repositories.interfaces import MonitorRepository
from app.repositories.memory import InMemoryMonitorRepository
from app.services.notifier import LocalLoggingNotifier, NotificationPublisher
from app.services.queue import InMemoryQueueClient, QueueClient

repository: MonitorRepository
queue: QueueClient
notifier: NotificationPublisher

if settings.aws_runtime_enabled:
    from app.aws.runtime import DynamoDBMonitorRepository, SNSNotifier, SQSQueueClient

    repository = DynamoDBMonitorRepository(
        settings.monitors_table or "",
        settings.check_results_table or "",
        settings.aws_region or "",
        settings.result_ttl_days,
    )
    queue = SQSQueueClient(settings.queue_url or "", settings.aws_region or "")
    notifier = SNSNotifier(settings.alerts_topic_arn or "", settings.aws_region or "")
else:
    repository = InMemoryMonitorRepository()
    queue = InMemoryQueueClient()
    notifier = LocalLoggingNotifier()
