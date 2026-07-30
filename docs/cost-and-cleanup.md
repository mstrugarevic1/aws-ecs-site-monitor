# Cost and Cleanup

Terraform is structured for a small demo environment, not a production baseline.

Cost-conscious choices in the prepared infrastructure:

- public subnets without a NAT Gateway;
- DynamoDB on-demand billing;
- SQS/SNS instead of running a broker;
- no RDS or ElastiCache;
- short CloudWatch log retention;
- one API task and one worker task by default.

No AWS resources have been created from this repository, so there is no repository-specific cleanup command to run yet. If the Terraform is applied later, cleanup should be handled with the same remote state and approval process used for deployment.
