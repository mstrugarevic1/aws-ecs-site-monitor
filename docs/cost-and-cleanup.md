# Cost And Cleanup

This is a portfolio lab design. Terraform is not applied in Phase 4.

Prepared cost-conscious choices:

- no NAT Gateway
- no RDS
- no ElastiCache
- short CloudWatch log retention
- one API task and one worker task by default
- DynamoDB on-demand billing

Future cleanup, after deployment is approved, will be documented before any destroy command is added or run.

