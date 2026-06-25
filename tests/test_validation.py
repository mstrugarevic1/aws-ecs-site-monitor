import pytest

from app.api.schemas import MonitorCreate
from app.domain.validation import validate_target_url


def test_monitor_input_validation_accepts_valid_payload() -> None:
    payload = MonitorCreate(
        name="Example API",
        url="https://example.com/health",
        expected_status=200,
        timeout_seconds=5,
        failure_threshold=3,
        enabled=True,
    )

    assert payload.url == "https://example.com/health"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("timeout_seconds", 31),
        ("failure_threshold", 11),
        ("expected_status", 99),
    ],
)
def test_monitor_input_validation_rejects_bad_values(field: str, value: object) -> None:
    data = {
        "name": "Example API",
        "url": "https://example.com/health",
        "expected_status": 200,
        "timeout_seconds": 5,
        "failure_threshold": 3,
        "enabled": True,
    }
    data[field] = value

    with pytest.raises(ValueError):
        MonitorCreate(**data)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/health",
        "https:///missing-host",
        "http://localhost/health",
        "http://127.0.0.1/health",
        "http://169.254.1.1/health",
        "http://10.0.0.1/health",
        "http://172.16.0.1/health",
        "http://192.168.1.10/health",
    ],
)
def test_url_safety_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(ValueError):
        validate_target_url(url)


def test_url_safety_allows_private_ip_when_explicitly_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "true")

    assert validate_target_url("http://10.0.0.1/health") == "http://10.0.0.1/health"
