# Implementation Notes

- Runtime selection lives in `app.runtime`.
- Local runtime uses in-memory repository, queue, and logging notifier adapters.
- AWS runtime is selected only when `AWS_REGION`, `MONITORS_TABLE`, `CHECK_RESULTS_TABLE`, `QUEUE_URL`, and `ALERTS_TOPIC_ARN` are all set.
- AWS adapters import `boto3` only when AWS runtime is selected, so local tests do not need AWS credentials.
- The project targets Python 3.12-compatible code.
- `terraform init -backend=false` still needs provider registry access, but not AWS credentials.
- Validation commands should run tools through `.venv/bin/python -m ...` when possible, because copied virtualenv console scripts can contain stale shebang paths.
- Missing production features are intentional for the demo scope; see [Limitations](limitations.md).
