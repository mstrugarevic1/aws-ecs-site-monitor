# Limitations

- Not production-ready.
- AWS deployment has not been proven from this repository.
- Local API, scheduler, and worker processes do not share in-memory state.
- AWS-backed runtime is required for shared queue and repository state across roles.
- No authentication or authorization is implemented.
- HTTPS, custom domain, and ACM certificate are not configured.
- Full SSRF protection is not implemented.
- No multi-region or high-availability claims are made.
