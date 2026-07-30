import importlib
import sys
import types
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.repositories.memory import InMemoryMonitorRepository
from app.services.notifier import LocalLoggingNotifier
from app.services.queue import InMemoryQueueClient

AWS_RUNTIME_ENV = (
    "AWS_REGION",
    "MONITORS_TABLE",
    "CHECK_RESULTS_TABLE",
    "QUEUE_URL",
    "ALERTS_TOPIC_ARN",
)


@pytest.fixture(autouse=True)
def local_runtime_env(monkeypatch):
    for name in AWS_RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)
    reload_api_main()


def reload_api_main():
    import app.api.main
    import app.common.config
    import app.runtime

    importlib.reload(app.common.config)
    importlib.reload(app.runtime)
    return importlib.reload(app.api.main)


def create_test_app():
    return reload_api_main().create_app()


def install_fake_boto3(monkeypatch) -> None:
    boto3 = types.ModuleType("boto3")
    dynamodb = types.ModuleType("boto3.dynamodb")
    conditions = types.ModuleType("boto3.dynamodb.conditions")

    def client(*args: object, **kwargs: object) -> object:
        return object()

    def resource(*args: object, **kwargs: object) -> types.SimpleNamespace:
        return types.SimpleNamespace(Table=lambda name: object())

    def key(name: str) -> types.SimpleNamespace:
        return types.SimpleNamespace(eq=lambda value: (name, value))

    cast(Any, boto3).client = client
    cast(Any, boto3).resource = resource
    cast(Any, conditions).Key = key
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setitem(sys.modules, "boto3.dynamodb", dynamodb)
    monkeypatch.setitem(sys.modules, "boto3.dynamodb.conditions", conditions)


def test_api_uses_local_runtime_without_aws_env(monkeypatch) -> None:
    for name in AWS_RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)

    app = create_test_app()

    assert isinstance(app.state.repository, InMemoryMonitorRepository)
    assert isinstance(app.state.queue, InMemoryQueueClient)
    assert isinstance(app.state.notifier, LocalLoggingNotifier)


def test_api_uses_aws_runtime_when_all_aws_env_vars_exist(monkeypatch) -> None:
    for name in AWS_RUNTIME_ENV:
        monkeypatch.setenv(name, f"fake-{name.lower()}")
    install_fake_boto3(monkeypatch)

    app = reload_api_main().create_app()

    assert type(app.state.repository).__name__ == "DynamoDBMonitorRepository"
    assert type(app.state.queue).__name__ == "SQSQueueClient"
    assert type(app.state.notifier).__name__ == "SNSNotifier"


def test_health_readiness_version_and_dashboard() -> None:
    client = TestClient(create_test_app())

    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
    version = client.get("/version").json()
    assert version["name"] == "aws-ecs-internal-service-monitor"
    assert version["version"] == "0.1.0"

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Internal Service Monitor" in dashboard.text


def test_api_crud_manual_check_and_results() -> None:
    client = TestClient(create_test_app())
    payload = {
        "name": "Example API",
        "url": "https://example.com/health",
        "expected_status": 200,
        "timeout_seconds": 5,
        "failure_threshold": 3,
        "enabled": True,
    }

    created = client.post("/api/v1/monitors", json=payload)
    assert created.status_code == 201
    monitor = created.json()
    monitor_id = monitor["monitor_id"]
    assert monitor["status"] == "UNKNOWN"

    assert client.get("/api/v1/monitors").json()[0]["monitor_id"] == monitor_id
    assert client.get(f"/api/v1/monitors/{monitor_id}").json()["name"] == "Example API"

    patched = client.patch(f"/api/v1/monitors/{monitor_id}", json={"enabled": False})
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False

    check = client.post(f"/api/v1/monitors/{monitor_id}/check")
    assert check.status_code == 202
    assert check.json()["monitor_id"] == monitor_id

    results = client.get(f"/api/v1/monitors/{monitor_id}/results")
    assert results.status_code == 200
    assert results.json() == []

    deleted = client.delete(f"/api/v1/monitors/{monitor_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/monitors/{monitor_id}").status_code == 404


def test_api_rejects_unsafe_url() -> None:
    client = TestClient(create_test_app())

    response = client.post(
        "/api/v1/monitors",
        json={
            "name": "Unsafe",
            "url": "http://127.0.0.1/health",
            "expected_status": 200,
            "timeout_seconds": 5,
            "failure_threshold": 3,
            "enabled": True,
        },
    )

    assert response.status_code == 422
