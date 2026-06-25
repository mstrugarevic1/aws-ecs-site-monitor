# Observability

Phase 4 prepares CloudWatch alarms and a dashboard, but does not create them.

Prepared alarms:

- unhealthy ALB targets
- API running task count below desired count
- worker running task count below desired count
- SQS oldest message age
- DLQ visible messages
- ECS CPU usage
- ECS memory usage
- ALB 5xx errors

Prepared dashboard:

- ALB request count, 5xx, response time
- ECS CPU and memory
- SQS queue depth, oldest message age, DLQ count

