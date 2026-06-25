# Deployment

Phase 4 only prepares Terraform files. Do not deploy yet.

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

