from fastapi.testclient import TestClient


def test_register_and_list_current_user_organizations(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "correct horse battery staple",
            "display_name": "Admin",
            "organization_name": "Acme Corporation",
            "organization_slug": "acme",
        },
    )

    assert register_response.status_code == 201
    payload = register_response.json()
    organization_id = payload["memberships"][0]["organization_id"]
    access_token = payload["tokens"]["access_token"]

    list_response = client.get(
        "/organizations",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == organization_id
    assert list_response.json()[0]["slug"] == "acme"


def test_list_organizations_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/organizations")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.missing_token"


def test_organization_slug_conflict_returns_error_envelope(client: TestClient) -> None:
    first_response = client.post("/organizations", json={"name": "Security", "slug": "security"})
    second_response = client.post("/organizations", json={"name": "Security 2", "slug": "security"})

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "organization.slug_conflict"


def test_workspaces_are_scoped_to_organization(client: TestClient) -> None:
    session_a = client.post(
        "/auth/register",
        json={
            "email": "tenant-a@example.com",
            "password": "correct horse battery staple",
            "display_name": "Tenant A",
            "organization_name": "Company A",
        },
    ).json()
    session_b = client.post(
        "/auth/register",
        json={
            "email": "tenant-b@example.com",
            "password": "correct horse battery staple",
            "display_name": "Tenant B",
            "organization_name": "Company B",
        },
    ).json()
    org_a = {"id": session_a["memberships"][0]["organization_id"]}
    org_b = {"id": session_b["memberships"][0]["organization_id"]}

    create_a = client.post(
        f"/organizations/{org_a['id']}/workspaces",
        headers={"Authorization": f"Bearer {session_a['tokens']['access_token']}"},
        json={"name": "Engineering", "description": "Engineering knowledge base"},
    )
    create_b = client.post(
        f"/organizations/{org_b['id']}/workspaces",
        headers={"Authorization": f"Bearer {session_b['tokens']['access_token']}"},
        json={"name": "Engineering", "description": "Different tenant, same slug allowed"},
    )

    assert create_a.status_code == 201
    assert create_b.status_code == 201

    workspaces_a = client.get(
        f"/organizations/{org_a['id']}/workspaces",
        headers={"Authorization": f"Bearer {session_a['tokens']['access_token']}"},
    ).json()
    workspaces_b = client.get(
        f"/organizations/{org_b['id']}/workspaces",
        headers={"Authorization": f"Bearer {session_b['tokens']['access_token']}"},
    ).json()

    assert len(workspaces_a) == 1
    assert len(workspaces_b) == 1
    assert workspaces_a[0]["organization_id"] == org_a["id"]
    assert workspaces_b[0]["organization_id"] == org_b["id"]
    assert workspaces_a[0]["id"] != workspaces_b[0]["id"]


def test_cross_tenant_workspace_access_is_denied(client: TestClient) -> None:
    session_a = client.post(
        "/auth/register",
        json={
            "email": "cross-a@example.com",
            "password": "correct horse battery staple",
            "display_name": "Cross A",
            "organization_name": "Cross A Org",
        },
    ).json()
    session_b = client.post(
        "/auth/register",
        json={
            "email": "cross-b@example.com",
            "password": "correct horse battery staple",
            "display_name": "Cross B",
            "organization_name": "Cross B Org",
        },
    ).json()
    org_b_id = session_b["memberships"][0]["organization_id"]

    response = client.get(
        f"/organizations/{org_b_id}/workspaces",
        headers={"Authorization": f"Bearer {session_a['tokens']['access_token']}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.permission_denied"
