# Security Policy

This repository is a controlled portfolio project.

Current state:

- no secrets are committed
- no AWS credentials are required for local development
- deployment workflows are prepared but manually gated
- Terraform uses local state during development

If a secret is ever committed by mistake, rotate it immediately and remove it from the repository history before any further use.

