from fastapi.testclient import TestClient


def test_register_bootstraps_user_organization_and_tokens(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "correct horse battery staple",
            "display_name": "Admin User",
            "organization_name": "Acme Security",
            "organization_slug": "acme-security",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == "admin@example.com"
    assert payload["tokens"]["token_type"] == "bearer"  # noqa: S105
    assert payload["tokens"]["access_token"]
    assert payload["tokens"]["refresh_token"]
    assert payload["memberships"][0]["role"] == "organization_admin"
    assert "workspaces.create" in payload["memberships"][0]["permissions"]


def test_login_and_me_return_memberships(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "correct horse battery staple",
            "display_name": "Owner",
            "organization_name": "Owner Org",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "owner@example.com", "password": "correct horse battery staple"},
    )

    assert login_response.status_code == 200
    access_token = login_response.json()["tokens"]["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == "owner@example.com"
    assert me_response.json()["memberships"][0]["role"] == "organization_admin"


def test_refresh_requires_refresh_token_type(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "correct horse battery staple",
            "display_name": "Refresh User",
            "organization_name": "Refresh Org",
        },
    )
    tokens = register_response.json()["tokens"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    wrong_type_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]
    assert wrong_type_response.status_code == 401
    assert wrong_type_response.json()["error"]["code"] == "auth.invalid_token_type"
