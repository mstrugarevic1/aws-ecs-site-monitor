# Security Considerations

Phase 4 creates Terraform files only.

Prepared controls:

- separate ECS task roles for API, scheduler, and worker
- GitHub OIDC planned for later, no static AWS keys
- ECR scan on push
- DynamoDB, SQS, SNS encryption using AWS-managed options
- API tasks accept inbound traffic only from the ALB security group
- worker and scheduler tasks have no inbound rules

IAM wildcard note: no broad resource wildcard is used in the prepared task role policies. AWS-managed task execution policy is attached for ECS image pull and log delivery.

HTTP is a lab limitation until a domain and ACM certificate are provided.

