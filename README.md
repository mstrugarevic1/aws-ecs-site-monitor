# aws-ecs-internal-service-monitor

[![CI](https://github.com/mstrugarevic1/aws-ecs-internal-service-monitor/actions/workflows/pr.yml/badge.svg)](https://github.com/mstrugarevic1/aws-ecs-internal-service-monitor/actions/workflows/pr.yml)

Production-oriented learning project demonstrating common AWS ECS operational patterns.

This project is a small distributed HTTP service-monitoring system intended for AWS ECS Fargate. It is not production-ready. No AWS resources are deployed during the initial project-development phases.

## Architecture

![AWS ECS Internal Service Monitor Architecture](docs/images/aws-ecs-internal-service-monitor-architecture.png)

The system uses one Python codebase and one container image with three runtime commands:

- Monitor API Service: FastAPI CRUD API, manual check requests, health/readiness/version endpoints, and a Jinja2 dashboard.
- Scheduler Task: intended for EventBridge every five minutes; enqueues one check job per enabled monitor.
- Checker Worker Service: consumes check jobs, performs HTTP checks, updates monitor state, stores results, and emits alert/recovery notifications.

Future AWS deployment uses ECS Fargate, SQS, DynamoDB, SNS, EventBridge, ALB, ECR, IAM, and CloudWatch. Current local mode uses in-memory repositories and queue implementations.

Future CI/CD path:

```text
Pull Request -> Ruff/mypy/pytest -> Docker build -> Trivy -> Terraform validate

Manual Dispatch -> aws-dev approval -> GitHub OIDC -> ECR push -> ECS update
```

The deployment path is prepared but disabled by default. It requires explicit workflow input and approval variables before any AWS step can run.

## Features

- monitor CRUD API
- URL validation with basic SSRF safeguards
- in-memory local storage
- local queue with retry and dead-letter behavior
- HTTP checks with timeouts through `httpx`
- failure threshold and recovery notification logic
- structured JSON logging formatter
- Dockerfile and Docker Compose
- Terraform files for future AWS infrastructure
- pull request CI workflow with Ruff, mypy, pytest, Docker build, and Trivy scans

## Repository Layout

```text
app/
├── api/
├── aws/
├── common/
├── domain/
├── repositories/
├── scheduler/
├── services/
├── templates/
└── worker/
docs/
terraform/
tests/
```

## Local Quick Start

```bash
make install
make test
make run-api
```

Open:

```text
http://127.0.0.1:8000/
```

Docker:

```bash
make docker-build
make docker-up
make docker-down
```

The default Compose service runs the API. Scheduler and worker containers are available under the `jobs` profile, but local state is still process-local.

## API Examples

Create a monitor:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/monitors \
  -H 'content-type: application/json' \
  -d '{"name":"Example API","url":"https://example.com/health","expected_status":200,"timeout_seconds":5,"failure_threshold":3,"enabled":true}'
```

List monitors:

```bash
curl http://127.0.0.1:8000/api/v1/monitors
```

Request a manual check:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/monitors/MONITOR_ID/check
```

Health endpoints:

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
curl http://127.0.0.1:8000/version
```

## Local Validation

```bash
make lint
make typecheck
make test
make terraform-format
make terraform-validate
```

`terraform validate` is designed to run locally with `init -backend=false`. On this workstation, provider initialization succeeds but provider schema loading currently fails with `Unrecognized remote plugin message`; no AWS access is required or used.

## Future AWS Deployment

Terraform files are prepared under `terraform/environments/dev`, but deployment is intentionally disabled for now.

Do not run yet:

- `terraform plan`
- `terraform apply`
- `terraform destroy`
- AWS CLI resource changes
- ECR pushes
- ECS service updates

Remote Terraform state is not configured. A commented future example exists at:

```text
terraform/environments/dev/backend.tf.example
```

## Security

- No AWS credentials are stored or required for local development.
- Future deployment is intended to use GitHub OIDC, not static access keys.
- Containers run as a non-root user.
- ECR scan-on-push is prepared in Terraform.
- DynamoDB, SQS, and SNS encryption are prepared with AWS-managed encryption.
- API ECS tasks accept inbound traffic only from the ALB security group.
- Worker and scheduler tasks have no inbound security group rules.

This is a controlled internal tool. It includes basic SSRF safeguards but does not implement full SSRF protection. Private IP literals are rejected unless `ALLOW_PRIVATE_TARGETS=true` is set.

HTTP is a lab limitation until a domain and ACM certificate are provided.

## Cost Notes

The future AWS design avoids NAT Gateway, RDS, ElastiCache, Route 53 requirements, and paid third-party monitoring. Expected cost drivers after deployment approval are ALB, ECS Fargate tasks, CloudWatch logs/alarms/dashboard, DynamoDB, SQS, SNS, and ECR storage.

## Current Status

Completed locally:

- Phase 1: domain models, in-memory storage, API CRUD, health endpoints, dashboard, tests
- Phase 2: scheduler, worker, queue abstraction, HTTP checks, alerts, tests
- Phase 3: Dockerfile, Docker Compose, Makefile, lint/typecheck, PR CI workflow
- Phase 4: Terraform infrastructure files and local formatting/init validation attempt
- Phase 5: disabled/manual GitHub deployment and Terraform workflow files

Next:

- Phase 6: failure scenarios, screenshot placeholders, final documentation, and final local validation
