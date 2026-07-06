from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_metrics_endpoint_records_http_counts_and_latency(client: TestClient) -> None:
    health_response = client.get("/health/live")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers["content-type"]
    body = metrics_response.text
    assert "# TYPE eakp_http_requests_total counter" in body
    assert (
        'eakp_http_requests_total{method="GET",path="/health/live",status_code="200"} 1'
        in body
    )
    assert (
        'eakp_http_request_latency_ms_sum{method="GET",path="/health/live",'
        'status_code="200"}'
        in body
    )


def test_metrics_use_route_templates_for_dynamic_paths(client: TestClient) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]

    workspace_response = client.post(
        f"/organizations/{organization_id}/workspaces",
        headers=_auth(token),
        json={"name": "Metrics Knowledge"},
    )
    metrics_response = client.get("/metrics")

    assert workspace_response.status_code == 201
    body = metrics_response.text
    assert "/workspaces" in body
    assert organization_id not in body
    assert (
        'eakp_http_requests_total{method="POST",'
        'path="/organizations/{organization_id}/workspaces",status_code="201"} 1'
        in body
    )


def _register(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": "metrics@example.com",
            "password": "correct horse battery staple",
            "display_name": "Metrics User",
            "organization_name": "Metrics Org",
        },
    )
    assert response.status_code == 201
    return dict(response.json())


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
