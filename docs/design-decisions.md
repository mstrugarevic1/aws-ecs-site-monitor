# Design Decisions

The project uses:

- ECS Fargate instead of Kubernetes: lower operational overhead for a portfolio lab and no cluster management.
- SQS instead of direct synchronous checker calls: it decouples scheduler and worker failure domains and gives retry/DLQ behavior.
- DynamoDB instead of RDS: simpler operational model, lower cost, and a better fit for key/value monitor state and time-ordered results.
- one image with multiple commands: keeps the codebase and deployment artifact small while still showing three runtime roles.
- EventBridge Scheduler: a simple managed trigger for periodic checks.
- public subnets as a lab cost compromise: avoids a NAT Gateway while still demonstrating the AWS network shape.
- server-rendered HTML instead of a frontend framework: the portfolio goal is DevOps, not frontend complexity.
- in-memory or local services before real AWS integration: makes the project runnable without AWS access and keeps the early phases testable.

