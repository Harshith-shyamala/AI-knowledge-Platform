from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_search_returns_citation_ready_results(client: TestClient) -> None:
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
        _search_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"query": "SOC 2 evidence", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "SOC 2 evidence"
    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["document_id"] == document["id"]
    assert result["document_version_id"]
    assert result["chunk_id"]
    assert result["lexical_score"] > 0
    assert result["score"] > 0
    assert "SOC 2 evidence" in result["content"]


def test_search_is_scoped_to_current_tenant(client: TestClient) -> None:
    session_a = _register(client, email="search-a@example.com", org_name="Search A Org")
    session_b = _register(client, email="search-b@example.com", org_name="Search B Org")
    org_a = session_a["memberships"][0]["organization_id"]
    org_b = session_b["memberships"][0]["organization_id"]
    token_a = session_a["tokens"]["access_token"]
    token_b = session_b["tokens"]["access_token"]
    workspace_a = _create_workspace(client, org_a, token_a)["id"]
    workspace_b = _create_workspace(client, org_b, token_b)["id"]

    doc_a = _upload_document(
        client,
        org_a,
        workspace_a,
        token_a,
        title="Alpha Policy",
        body="Alpha tenant secret launch policy.",
    )
    doc_b = _upload_document(
        client,
        org_b,
        workspace_b,
        token_b,
        title="Beta Policy",
        body="Beta tenant vendor policy.",
    )
    _index_document(client, org_a, workspace_a, doc_a["id"], token_a)
    _index_document(client, org_b, workspace_b, doc_b["id"], token_b)

    denied = client.post(
        _search_url(org_b, workspace_b),
        headers=_auth(token_a),
        json={"query": "Beta", "top_k": 5},
    )
    allowed = client.post(
        _search_url(org_a, workspace_a),
        headers=_auth(token_a),
        json={"query": "Beta", "top_k": 5},
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "auth.permission_denied"
    assert allowed.status_code == 200
    assert allowed.json()["results"] == []


def test_search_ignores_unindexed_documents(client: TestClient) -> None:
    session = _register(client, email="unindexed@example.com", org_name="Unindexed Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    _upload_document(
        client,
        organization_id,
        workspace_id,
        token,
        title="Unindexed",
        body="This document mentions unretrievable evidence.",
    )

    response = client.post(
        _search_url(organization_id, workspace_id),
        headers=_auth(token),
        json={"query": "unretrievable evidence", "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


def _register(
    client: TestClient,
    email: str = "search@example.com",
    org_name: str = "Search Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Search User",
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


def _search_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/search"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
