# Deployment

Phase 5 prepares deployment workflow files. Do not deploy yet.

Allowed local validation:

```bash
make terraform-format
make terraform-validate
```

Not allowed until explicitly approved:

- `terraform plan`
- `terraform apply`
- `terraform destroy`
- AWS CLI resource changes
- ECR image push
- ECS service updates
- remote Terraform state

Future deployment will require GitHub OIDC, an ECR image tagged with a Git SHA, and protected approval before any AWS command runs.

Prepared CI/CD flow:

```text
Developer
  |
  +-- pull request ----------------------+
  |                                      |
  |                                      v
  |                              GitHub Actions PR checks
  |                              - Ruff format/lint
  |                              - mypy
  |                              - pytest
  |                              - Docker build
  |                              - Trivy scans
  |                              - Terraform fmt/init/validate
  |
  +-- manual dispatch only --------------+
                                         |
                                         v
                              Future protected aws-dev deployment
                              - requires deployment_enabled=true
                              - requires AWS_DEPLOYMENT_APPROVED=true
                              - requires GitHub OIDC trust
                              - refuses placeholder image tags
```

Prepared Terraform workflow:

```text
Pull request touching terraform/
  |
  v
fmt -> init -backend=false -> validate

Manual future AWS plan/apply/destroy
  |
  v
requires explicit boolean input + aws-dev environment + AWS_TERRAFORM_APPROVED=true
```

The deployment workflow is intentionally manual-only and has no push trigger.
