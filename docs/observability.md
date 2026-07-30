# Observability

Terraform defines CloudWatch log groups for the API, scheduler, and worker containers.

Prepared CloudWatch alarms cover:

- unhealthy ALB targets;
- API and worker running task counts;
- SQS oldest message age;
- DLQ visible messages;
- ECS CPU and memory usage;
- ALB 5xx errors.

The prepared dashboard includes ALB request/error/latency metrics, ECS CPU and memory metrics, and SQS queue depth/age/DLQ metrics.

These resources are defined in Terraform but have not been deployed from this repository.
