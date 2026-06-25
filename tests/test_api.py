from fastapi.testclient import TestClient

from app.api.main import create_app


def test_health_readiness_version_and_dashboard() -> None:
    client = TestClient(create_app())

    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
    version = client.get("/version").json()
    assert version["name"] == "aws-ecs-internal-service-monitor"
    assert version["version"] == "0.1.0"

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Internal Service Monitor" in dashboard.text


def test_api_crud_manual_check_and_results() -> None:
    client = TestClient(create_app())
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
    client = TestClient(create_app())

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
