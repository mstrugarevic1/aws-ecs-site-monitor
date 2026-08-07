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

Run the bootstrap once from a trusted workstation before adding a deployment workflow. It requires AWS CLI v2, GitHub CLI, an authenticated GitHub session with repository administration access, and a named AWS CLI profile allowed to create S3, DynamoDB, IAM, and OIDC resources.

```bash
AWS_PROFILE=my-profile \
GITHUB_REPOSITORY=owner/aws-ecs-site-monitor \
./scripts/bootstrap-deployment.sh
```

Use `./scripts/bootstrap-deployment.sh --help` for optional names and region settings. The script asks for confirmation, is safe to rerun, and never creates or stores AWS access keys.

It creates or updates:

- an encrypted, versioned, private S3 Terraform-state bucket;
- a DynamoDB Terraform-lock table;
- the GitHub Actions OIDC provider;
- a repository- and environment-scoped deployment role;
- the `aws-dev` GitHub environment and its non-secret deployment variables.

The role can manage the AWS services used by this project and IAM roles beginning with the configured project prefix. Use a dedicated AWS account or tighten the generated inline policy if other workloads share the account.

After bootstrap, configure required reviewers for the `aws-dev` environment in GitHub. The script does not deploy the application or configure environment protection rules.

The deployment workflow still needs to:

- initialize Terraform with the generated backend variables;
- create ECR before the first image push;
- build and push an immutable image tagged with the Git commit SHA;
- apply Terraform with that image URI;
- verify ECS stability and `/healthz`.

Do not use the default local image value for a real ECS deployment.
