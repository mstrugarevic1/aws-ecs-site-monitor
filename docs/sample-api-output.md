# Sample API Output

Create a monitor:

```json
{
  "monitor_id": "3d33f8c1-0f77-4d1f-9c7c-8dbf7a7b65df",
  "name": "Example API",
  "url": "https://example.com/health",
  "expected_status": 200,
  "timeout_seconds": 5,
  "failure_threshold": 3,
  "enabled": true,
  "status": "UNKNOWN",
  "latency_ms": null,
  "consecutive_failures": 0,
  "created_at": "2026-06-25T00:00:00Z",
  "updated_at": "2026-06-25T00:00:00Z",
  "last_checked_at": null,
  "last_success_at": null
}
```

Check result:

```json
[
  {
    "monitor_id": "3d33f8c1-0f77-4d1f-9c7c-8dbf7a7b65df",
    "checked_at": "2026-06-25T00:05:00Z",
    "job_id": "b2a18b7f-6f74-4e0d-bf05-0d0a6c2e8c31",
    "status": "UP",
    "http_status": 200,
    "latency_ms": 42,
    "error_type": null,
    "error_message": null
  }
]
```

