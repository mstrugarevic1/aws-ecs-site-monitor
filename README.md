# AWS ECS Internal Service Monitor

Internal HTTP service monitoring system designed for AWS ECS/Fargate.

Users define HTTP monitors through a FastAPI API. A scheduler enqueues checks for enabled monitors. Workers consume queued checks, call target endpoints, store results, and emit alerts when failure thresholds are reached. The same Docker image can run as the API, scheduler, or worker depending on the command and runtime configuration.

## Architecture

The project demonstrates a small ECS service split into three roles:

- API: dashboard, monitor CRUD, readiness, manual check enqueueing.
- Scheduler: periodically scans enabled monitors and sends check jobs.
- Worker: consumes jobs, runs HTTP checks, writes results, updates monitor state, and publishes alert or recovery notifications.

AWS-backed runtime targets:

- ALB routes HTTP traffic to the API service.
- EventBridge runs the scheduler task on a schedule.
- SQS decouples check production from worker execution.
- DynamoDB stores monitor definitions and check results.
- SNS receives alert and recovery notifications.
- CloudWatch receives logs, alarms, and dashboard metrics.
- Terraform defines the AWS infrastructure.
- GitHub Actions runs validation.

![AWS ECS Internal Service Monitor Architecture](docs/images/aws-ecs-internal-service-monitor-architecture.png)

See [Architecture](docs/architecture.md) for the request and check flow.

## What This Demonstrates

- ECS/Fargate service decomposition with one reusable image.
- Queue-based worker processing with SQS.
- DynamoDB-backed state for monitors and check history.
- SNS alerting on threshold crossings and recovery.
- Runtime separation between local in-memory adapters and AWS adapters.
- Terraform infrastructure definition for the target AWS shape.
- CI validation for Python code and Terraform syntax.

## Current Status

- Local runtime works without AWS credentials.
- AWS runtime adapters are implemented for DynamoDB, SQS, and SNS.
- Terraform for the AWS environment is present and intended for deployment.
- AWS deployment has not been proven from this repository.

## Documentation

- [Architecture](docs/architecture.md)
- [Local Development](docs/local-development.md)
- [Deployment](docs/deployment.md)
- [Observability](docs/observability.md)
- [Security Considerations](docs/security-considerations.md)
- [Limitations](docs/limitations.md)
- [Cost and Cleanup](docs/cost-and-cleanup.md)
- [Implementation Notes](docs/implementation-notes.md)

## Limitations

- Not production-ready.
- No authentication is implemented.
- HTTPS, custom domain, and ACM certificate are not configured.
- Local API, scheduler, and worker processes do not share in-memory state.
- AWS-backed runtime is required for shared queue and repository state.
