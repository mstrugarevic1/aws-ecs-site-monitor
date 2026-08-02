# Deployment

Terraform defines the target AWS environment for Site Monitor, but this repository has not completed an AWS deployment.

Local validation:

```bash
make terraform-format
make terraform-validate
```

`make terraform-validate` runs `terraform init -backend=false` before validation, so it needs access to `registry.terraform.io` to download providers. It does not require AWS credentials.

## Current State

- Terraform modules define networking, ECR, DynamoDB, SQS/SNS, ECS/Fargate, ALB, EventBridge scheduling, IAM, and CloudWatch resources for the API, scheduler, and worker roles.
- Terraform uses local validation settings in this repository.
- Remote Terraform state is not configured.
- GitHub OIDC trust for AWS deployment is not configured.
- No `terraform apply` has been run from this repository.

## Before Deployment

Before applying this infrastructure, configure:

- remote Terraform state and locking;
- AWS account and region values;
- immutable image URI from ECR;
- notification email or another SNS subscriber;
- GitHub OIDC role trust, if deployment is automated later.

Do not use the default local image value for a real ECS deployment.
