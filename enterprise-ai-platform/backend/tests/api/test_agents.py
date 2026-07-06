from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_agent_run_returns_answer_citations_and_trace(client: TestClient) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    document = _upload_document(
        client,
        organization_id,
        workspace_id,
        token,
        title="Access Review Policy",
        body="Quarterly access reviews require manager approval and audit evidence.",
    )
    _index_document(client, organization_id, workspace_id, document["id"], token)

    response = client.post(
        _agent_runs_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"question": "What do quarterly access reviews require?", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "manager approval and audit evidence" in payload["answer"]
    assert payload["prompt_version"] == "agent-rag-v1"
    assert payload["workflow_version"] == "deterministic-agent-v1"
    assert [step["name"] for step in payload["steps"]] == [
        "plan",
        "search_workspace",
        "inspect_evidence",
        "grounding_reflection",
        "final_answer",
    ]
    assert payload["steps"][1]["metadata"]["result_count"] == "1"
    assert payload["steps"][3]["metadata"]["grounded"] == "true"
    assert len(payload["citations"]) == 1
    assert payload["citations"][0]["document_id"] == document["id"]


def test_agent_run_can_hide_trace(client: TestClient) -> None:
    session = _register(client, email="agent-hidden@example.com", org_name="Agent Hidden Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _agent_runs_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"question": "What indexed evidence exists?", "include_trace": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["steps"] == []
    assert payload["citations"] == []
    assert "not have enough indexed knowledge" in payload["answer"]


def test_agent_run_is_tenant_authorized(client: TestClient) -> None:
    session_a = _register(client, email="agent-a@example.com", org_name="Agent A Org")
    session_b = _register(client, email="agent-b@example.com", org_name="Agent B Org")
    token_a = session_a["tokens"]["access_token"]
    token_b = session_b["tokens"]["access_token"]
    org_b = session_b["memberships"][0]["organization_id"]
    workspace_b = _create_workspace(client, org_b, token_b)["id"]

    denied = client.post(
        _agent_runs_url(org_b, workspace_b),
        headers=_auth(token_a),
        json={"question": "Can I see another tenant?"},
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "auth.permission_denied"


def _register(
    client: TestClient,
    email: str = "agent@example.com",
    org_name: str = "Agent Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Agent User",
            "organization_name": org_name,
        },
    )
    assert response.status_code == 201
    return dict(response.json())


def _create_workspace(client: TestClient, organization_id: str, token: str) -> dict[str, Any]:
    response = client.post(
        f"/organizations/{organization_id}/workspaces",
        headers=_auth(token),
        json={"name": "Knowledge"},
    )
    assert response.status_code == 201
    return dict(response.json())


def _upload_document(
    client: TestClient,
    organization_id: str,
    workspace_id: str,
    token: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    response = client.post(
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents",
        headers=_auth(token),
        data={"title": title},
        files={"file": ("policy.md", body.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201
    return dict(response.json()["document"])


def _index_document(
    client: TestClient,
    organization_id: str,
    workspace_id: str,
    document_id: str,
    token: str,
) -> None:
    response = client.post(
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/index",
        headers=_auth(token),
    )
    assert response.status_code == 200


def _agent_runs_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/agents/runs"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
