# Limitations

- This is not production-ready.
- Full SSRF protection is intentionally not implemented yet.
- Local development uses in-memory repositories and queue implementations, so the API, scheduler, and worker do not share state across separate processes until the AWS-backed phase.
- HTTPS is not configured in the current implementation because no domain or ACM certificate is provided.
- Terraform is validated locally only; AWS deployment is intentionally disabled until explicitly approved.

