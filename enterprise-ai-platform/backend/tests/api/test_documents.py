from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings


def test_upload_list_and_version_document(
    client: TestClient,
    test_settings: Settings,
) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace = _create_workspace(client, organization_id, token)
    workspace_id = workspace["id"]

    upload_response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Security Policy"},
        files={"file": ("security.md", b"# Security\nAll vendors need review.", "text/markdown")},
    )

    assert upload_response.status_code == 201
    upload = upload_response.json()
    document = upload["document"]
    version = upload["version"]
    assert document["title"] == "Security Policy"
    assert document["status"] == "uploaded"
    assert version["version_number"] == 1
    assert version["file_sha256"]
    assert (Path(test_settings.storage_root) / version["storage_key"]).read_bytes() == (
        b"# Security\nAll vendors need review."
    )

    list_response = client.get(_documents_url(organization_id, workspace_id), headers=_auth(token))

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [document["id"]]

    version_response = client.post(
        f"{_documents_url(organization_id, workspace_id)}/{document['id']}/versions",
        headers=_auth(token),
        files={"file": ("security-v2.md", b"# Security\nReview every year.", "text/markdown")},
    )

    assert version_response.status_code == 201
    assert version_response.json()["version"]["version_number"] == 2
    assert version_response.json()["document"]["current_version_id"] == version_response.json()[
        "version"
    ]["id"]

    versions_response = client.get(
        f"{_documents_url(organization_id, workspace_id)}/{document['id']}/versions",
        headers=_auth(token),
    )

    assert versions_response.status_code == 200
    assert [item["version_number"] for item in versions_response.json()] == [1, 2]


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    session = _register(client, email="unsupported@example.com", org_name="Unsupported Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "document.unsupported_file_type"


def test_upload_accepts_markdown_with_generic_browser_mime_type(client: TestClient) -> None:
    session = _register(client, email="generic-mime@example.com", org_name="Generic MIME Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Browser Markdown"},
        files={
            "file": (
                "README.md",
                b"# Browser upload\nMarkdown files can have generic MIME types.",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 201
    document = response.json()["document"]
    assert document["title"] == "Browser Markdown"
    assert document["mime_type"] == "text/markdown"


def test_upload_accepts_markdown_browser_mime_aliases(client: TestClient) -> None:
    session = _register(client, email="markdown-alias@example.com", org_name="Markdown Alias Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Vendor Security Policy"},
        files={
            "file": (
                "vendor-security-policy.md",
                b"# Vendor Security Policy\nAll vendors need review.",
                "text/x-markdown",
            )
        },
    )

    assert response.status_code == 201
    document = response.json()["document"]
    assert document["title"] == "Vendor Security Policy"
    assert document["mime_type"] == "text/markdown"


def test_upload_normalizes_markdown_sent_as_text_plain(client: TestClient) -> None:
    session = _register(
        client,
        email="markdown-text-plain@example.com",
        org_name="Markdown Text Plain Org",
    )
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Plain Browser Markdown"},
        files={
            "file": (
                "README.md",
                b"# Browser upload\nThis Markdown arrived as text/plain.",
                "text/plain; charset=utf-8",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["document"]["mime_type"] == "text/markdown"


def test_upload_accepts_json_document(client: TestClient) -> None:
    session = _register(client, email="json-doc@example.com", org_name="JSON Docs Org")
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _documents_url(organization_id, workspace_id),
        headers=_auth(token),
        data={"title": "Security Controls"},
        files={
            "file": (
                "controls.json",
                b'{"policy": "vendor security", "review": "quarterly"}',
                "application/json",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["document"]["mime_type"] == "application/json"


def test_upload_requires_document_permission(client: TestClient) -> None:
    session_a = _register(client, email="doc-a@example.com", org_name="Doc A Org")
    session_b = _register(client, email="doc-b@example.com", org_name="Doc B Org")
    org_b = session_b["memberships"][0]["organization_id"]
    workspace_b = _create_workspace(client, org_b, session_b["tokens"]["access_token"])

    response = client.post(
        _documents_url(org_b, workspace_b["id"]),
        headers=_auth(session_a["tokens"]["access_token"]),
        files={"file": ("notes.txt", b"tenant crossing", "text/plain")},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.permission_denied"


def _register(
    client: TestClient,
    email: str = "docs@example.com",
    org_name: str = "Docs Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Docs User",
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


def _documents_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/documents"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
