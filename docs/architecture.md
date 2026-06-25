# Architecture

Prepared future AWS shape:

```text
EventBridge -> ECS Scheduler Task -> SQS -> ECS Worker Service
                                             |
ALB -> ECS API Service ----------------------+
          |                                  |
          +------------ DynamoDB ------------+
                                             |
                                      SNS Alerts
```

The lab uses public subnets with public IP assignment to avoid NAT Gateway cost. Production should prefer private subnets with controlled egress.

