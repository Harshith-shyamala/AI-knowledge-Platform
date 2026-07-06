from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_index_document_creates_chunks_and_updates_status(client: TestClient) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    document = _upload_document(client, organization_id, workspace_id, token)

    response = client.post(
        f"{_documents_url(organization_id, workspace_id)}/{document['id']}/index",
        headers=_auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document"]["status"] == "indexed"
    assert payload["chunks_indexed"] >= 2
    assert payload["embeddings_indexed"] == payload["chunks_indexed"]
    assert payload["embedding_provider"] == "local"

    chunks_response = client.get(
        f"{_documents_url(organization_id, workspace_id)}/{document['id']}/chunks",
        headers=_auth(token),
    )

    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) == payload["chunks_indexed"]
    assert chunks[0]["chunk_index"] == 0
    assert "Vendor review" in chunks[0]["content"]


def test_indexing_requires_upload_permission(client: TestClient) -> None:
    session_a = _register(client, email="index-a@example.com", org_name="Index A Org")
    session_b = _register(client, email="index-b@example.com", org_name="Index B Org")
    org_b = session_b["memberships"][0]["organization_id"]
    workspace_b = _create_workspace(client, org_b, session_b["tokens"]["access_token"])
    document = _upload_document(
        client,
        org_b,
        workspace_b["id"],
        session_b["tokens"]["access_token"],
    )

    response = client.post(
        f"{_documents_url(org_b, workspace_b['id'])}/{document['id']}/index",
        headers=_auth(session_a["tokens"]["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.permission_denied"


def _register(
    client: TestClient,
    email: str = "index@example.com",
    org_name: str = "Index Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Index User",
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
) -> dict[str, Any]:
    body = (
        "Vendor review is required before onboarding. " * 120
        + "Security evidence must be renewed annually."
    )
    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Vendor Review Policy"},
        files={"file": ("vendor-review.md", body.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201
    return dict(response.json()["document"])


def _documents_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/documents"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
