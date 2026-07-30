# Runtime Wiring Final Check

## Scope

- API, scheduler, and worker should use the same runtime selection logic from `app.runtime`.
- Local mode must work without AWS credentials.
- AWS mode must only be selected when all five required env vars are present.
- No AWS deployment or infrastructure changes are part of this change.

## Files Changed

Expected files:

- `app/api/main.py`: API now defaults to runtime-selected repository, queue, and notifier.
- `tests/test_api.py`: API runtime wiring and env-isolated selection tests.
- `README.md`: local-mode process state limitation note.
- `Makefile`: validation target robustness only, using `.venv/bin/python -m mypy` and `.venv/bin/python -m pytest`.

Unexpected files:

- `lessons_learned.md`: changed in the working tree but should not be included in the runtime-wiring commit.

Not changed:

- `app/runtime.py`
- Terraform files
- AWS deployment files
- Docker Compose, LocalStack, Redis, or new infrastructure files
- Application business logic unrelated to runtime wiring

## Runtime Wiring Result

- `app/api/main.py` uses `app.runtime.repository`, `app.runtime.queue`, and `app.runtime.notifier` by default.
- `create_app()` remains testable with explicit `repository`, `queue`, and `notifier` overrides.
- API, scheduler, and worker now follow the same runtime decision path through `app.runtime`.

## Environment Selection

- Local mode is selected when AWS env vars are absent.
- AWS mode requires all five env vars:
  - `AWS_REGION`
  - `MONITORS_TABLE`
  - `CHECK_RESULTS_TABLE`
  - `QUEUE_URL`
  - `ALERTS_TOPIC_ARN`
- API tests avoid accidental AWS runtime selection during collection by not importing `create_app` at module import time and by clearing the AWS runtime env vars in an autouse fixture.

## Tests

- Test isolation clears all five AWS runtime env vars before each API test.
- The earlier `sys.modules.pop()` and parent-package attribute deletion were removed. The remaining reloads are limited to `app.common.config`, `app.runtime`, and `app.api.main`, which hold import-time runtime state.
- The AWS selection test sets all five required env vars, installs fake `boto3` modules with `monkeypatch`, reloads runtime wiring, and proves the API receives AWS adapter instances from `app.runtime`.
- The AWS selection test does not prove live AWS connectivity, IAM permissions, DynamoDB/SQS/SNS behavior, or deployment correctness.

## Validation

- `make lint`: passed
- `make typecheck`: passed, `Success: no issues found in 33 source files`
- `make test`: passed, `34 passed`

## Remaining Limitations

- AWS adapter selection is tested with fake/mocked `boto3`, not live AWS.
- Local API, scheduler, and worker processes do not share in-memory state unless AWS-backed runtime is used.
- No Terraform apply or AWS deploy was performed.

## Final Recommendation

Not ready to commit

Blockers:

- Remove or exclude `lessons_learned.md` from the runtime-wiring commit.
