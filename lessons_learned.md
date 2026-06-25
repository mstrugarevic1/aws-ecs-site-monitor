# Lessons Learned

- This workspace does not have Python 3.12 installed; Phase 1 was locally validated with Python 3.13 while keeping 3.12-compatible code.
- URL validation reads `ALLOW_PRIVATE_TARGETS` at validation time so tests and local runs can toggle it without module reloads.
- Naming repository methods after builtins such as `list` confused mypy; use explicit names like `list_monitors`.
- Local queue retry tests are enough for Phase 2; real SQS visibility timeout and DLQ behavior belongs in the AWS phase.
- Docker image builds require the local Docker daemon; Phase 3 could validate Compose syntax but not image build in this workspace.
- Local Terraform is 1.5.7 here, so the project constraint is `>= 1.5.0` instead of `>= 1.6.0`.
- `terraform init -backend=false` still needs registry access to download providers; it does not require AWS credentials.
- This local Terraform/provider runtime can download the AWS provider but fails to instantiate it during `validate` with `Unrecognized remote plugin message`.
- This project directory was not a git repo initially; initialize it before trying to push upstream.
