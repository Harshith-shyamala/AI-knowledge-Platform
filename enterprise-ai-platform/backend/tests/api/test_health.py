from fastapi.testclient import TestClient


def test_liveness_returns_service_metadata(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.json() == {
        "status": "ok",
        "service": "enterprise-ai-platform-api-test",
        "environment": "test",
        "version": "v1",
    }


def test_readiness_returns_ready_without_external_dependencies(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["service"] == "enterprise-ai-platform-api-test"
    assert payload["dependencies"] == []
    assert payload["latency_ms"] >= 0


def test_request_id_header_is_preserved(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "req-test-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-123"

