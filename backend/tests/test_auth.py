async def test_register_login_me_refresh_flow(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "trader@example.com",
            "password": "correct-horse-battery",
            "display_name": "Trader One",
        },
    )
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["email"] == "trader@example.com"
    assert body["roles"] == ["user"]

    duplicate_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "trader@example.com",
            "password": "another-password",
            "display_name": "Trader Two",
        },
    )
    assert duplicate_resp.status_code == 409
    assert duplicate_resp.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "correct-horse-battery"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert tokens["token_type"] == "bearer"

    bad_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "wrong-password"},
    )
    assert bad_login_resp.status_code == 401
    assert bad_login_resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "trader@example.com"

    no_auth_resp = await client.get("/api/v1/auth/me")
    assert no_auth_resp.status_code == 401

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    refresh_with_access_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert refresh_with_access_resp.status_code == 401
    assert refresh_with_access_resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


async def test_register_validation_error_shape(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "display_name": ""},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in body["error"]
