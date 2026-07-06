from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_chat_answers_with_persisted_citations(client: TestClient) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    document = _upload_document(
        client,
        organization_id,
        workspace_id,
        token,
        title="Vendor Security Policy",
        body="Vendor security review requires SOC 2 evidence before onboarding.",
    )
    _index_document(client, organization_id, workspace_id, document["id"], token)

    response = client.post(
        _chat_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"message": "What evidence is required before onboarding?", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation"]["title"] == "What evidence is required before onboarding?"
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert "SOC 2 evidence" in payload["assistant_message"]["content"]
    assert len(payload["citations"]) == 1
    citation = payload["citations"][0]
    assert citation["document_id"] == document["id"]
    assert citation["document_version_id"]
    assert citation["chunk_id"]
    assert "SOC 2 evidence" in citation["quote"]

    transcript = client.get(
        f"{_chat_url(organization_id, workspace_id)}/{payload['conversation']['id']}",
        headers=_auth(token),
    )
    assert transcript.status_code == 200
    messages = transcript.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["citations"][0]["chunk_id"] == citation["chunk_id"]


def test_chat_extracts_question_specific_answers_from_one_chunk(client: TestClient) -> None:
    session = _register(
        client,
        email="chat-specific@example.com",
        org_name="Chat Specific Org",
    )
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    document = _upload_document(
        client,
        organization_id,
        workspace_id,
        token,
        title="Vendor Security Policy",
        body=(
            "# Vendor Onboarding\n"
            "All vendors must complete a security review before onboarding. "
            "The review requires SOC 2 Type II evidence and data handling controls.\n\n"
            "# Incident Response\n"
            "Security incidents must be reported within 24 hours of discovery.\n\n"
            "# AI Usage\n"
            "AI tools may not process confidential customer data unless approved by Security "
            "and Legal."
        ),
    )
    _index_document(client, organization_id, workspace_id, document["id"], token)

    evidence_response = client.post(
        _chat_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"message": "What evidence is required before onboarding?", "top_k": 3},
    )
    incident_response = client.post(
        _chat_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"message": "How quickly must security incidents be reported?", "top_k": 3},
    )

    assert evidence_response.status_code == 200
    assert incident_response.status_code == 200
    evidence_answer = evidence_response.json()["assistant_message"]["content"]
    incident_answer = incident_response.json()["assistant_message"]["content"]
    assert "SOC 2 Type II evidence" in evidence_answer
    assert "within 24 hours" in incident_answer
    assert evidence_answer != incident_answer


def test_chat_falls_back_when_workspace_has_no_indexed_context(client: TestClient) -> None:
    session = _register(client, email="chat-empty@example.com", org_name="Chat Empty Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _chat_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"message": "What does our policy say about SOC 2?", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "not have enough indexed knowledge" in payload["assistant_message"]["content"]
    assert payload["citations"] == []
    assert payload["assistant_message"]["citations"] == []


def test_chat_conversation_ids_are_tenant_scoped(client: TestClient) -> None:
    session_a = _register(client, email="chat-a@example.com", org_name="Chat A Org")
    session_b = _register(client, email="chat-b@example.com", org_name="Chat B Org")
    token_a = session_a["tokens"]["access_token"]
    token_b = session_b["tokens"]["access_token"]
    org_a = session_a["memberships"][0]["organization_id"]
    org_b = session_b["memberships"][0]["organization_id"]
    workspace_a = _create_workspace(client, org_a, token_a)["id"]
    workspace_b = _create_workspace(client, org_b, token_b)["id"]

    first = client.post(
        _chat_url(org_a, workspace_a),
        headers=_auth(token_a),
        json={"message": "Start a private tenant conversation."},
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation"]["id"]

    denied = client.post(
        _chat_url(org_b, workspace_b),
        headers=_auth(token_b),
        json={"message": "Continue it.", "conversation_id": conversation_id},
    )

    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "chat.conversation_not_found"


def _register(
    client: TestClient,
    email: str = "chat@example.com",
    org_name: str = "Chat Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Chat User",
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


def _chat_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/chat"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
