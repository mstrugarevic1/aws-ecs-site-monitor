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
- Terraform declares an S3 backend; the deployment workflow supplies its bucket, key, region, and lock table.
- The bootstrap script prepares remote state, GitHub OIDC trust, and deployment variables.
- The deployment workflow is manually triggered and guarded by the `aws-dev` environment.
- No `terraform apply` has been run from this repository.

## Before Deployment

Run the bootstrap once from a trusted workstation before running the deployment workflow. It requires AWS CLI v2, GitHub CLI, an authenticated GitHub session with repository administration access, and a named AWS CLI profile allowed to create S3, DynamoDB, IAM, and OIDC resources.

```bash
AWS_PROFILE=my-profile \
GITHUB_REPOSITORY=owner/aws-ecs-site-monitor \
./scripts/bootstrap-deployment.sh
```

Use `./scripts/bootstrap-deployment.sh --help` for optional names, reviewer, and region settings. The script asks for confirmation, is safe to rerun, and never creates or stores AWS access keys.

It creates or updates:

- an encrypted, versioned, private S3 Terraform-state bucket;
- a DynamoDB Terraform-lock table;
- the GitHub Actions OIDC provider;
- a repository- and environment-scoped deployment role;
- the `aws-dev` GitHub environment, its required reviewer, and its non-secret deployment variables.

The role can manage the AWS services used by this project and IAM roles beginning with the configured project prefix. Use a dedicated AWS account or tighten the generated inline policy if other workloads share the account.

The authenticated GitHub user is the default reviewer and may approve their own deployment. Set `GITHUB_REVIEWER` when running the script to choose another repository user. The script does not deploy the application.

Optionally add a `NOTIFICATION_EMAIL` variable to the environment. AWS sends a confirmation message before that address receives SNS notifications.

## Deploy

Push the commit to `main`, open **Actions → Deploy → Run workflow**, enable `confirm_deploy`, and approve the `aws-dev` environment when prompted.

The workflow:

- authenticates to AWS with GitHub OIDC and no stored AWS access keys;
- initializes the remote Terraform backend and validates the configuration;
- creates ECR before the first image build;
- builds a Linux AMD64 image tagged with the Git commit SHA, or reuses that tag on a retry;
- plans and applies the complete Terraform configuration;
- waits for the API and worker ECS services;
- verifies `/healthz` through the ALB and writes its URL to the run summary.

The first ECR-only apply emits Terraform's targeted-apply warning. This is expected because the repository must exist before its first image can be pushed.

Do not use the default local image value for a real ECS deployment.
