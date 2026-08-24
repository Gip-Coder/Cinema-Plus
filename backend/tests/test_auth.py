import pytest
from fastapi import status


def test_register_and_login(client):
    # Test Registration
    reg_payload = {
        "username": "pytestuser",
        "email": "pytestuser@example.com",
        "password": "testpassword123",
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "pytestuser"
    assert data["data"]["email"] == "pytestuser@example.com"
    assert "id" in data["data"]

    # Test Duplicate Registration rejection
    response2 = client.post("/api/auth/register", json=reg_payload)
    assert response2.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
        getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
    )

    # Test Login with Invalid Credentials
    bad_login = client.post("/api/auth/login", json={"username": "pytestuser", "password": "wrongpassword"})
    assert bad_login.status_code == status.HTTP_401_UNAUTHORIZED

    # Test Login
    login_payload = {
        "username": "pytestuser",
        "password": "testpassword123",
    }
    response_login = client.post("/api/auth/login", json=login_payload)
    assert response_login.status_code == status.HTTP_200_OK
    login_data = response_login.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]
    token = login_data["data"]["access_token"]

    # Test Get Profile (/me)
    headers = {"Authorization": f"Bearer {token}"}
    response_me = client.get("/api/auth/me", headers=headers)
    assert response_me.status_code == status.HTTP_200_OK
    assert response_me.json()["data"]["username"] == "pytestuser"

    # Test Update Profile using JSON body (not query params)
    response_update = client.put(
        "/api/auth/profile",
        json={"username": "newusername", "email": "newemail@example.com"},
        headers=headers,
    )
    assert response_update.status_code == status.HTTP_200_OK
    assert response_update.json()["data"]["username"] == "newusername"
    assert response_update.json()["data"]["email"] == "newemail@example.com"

    # Re-login to get updated token
    response_login_new = client.post(
        "/api/auth/login",
        json={"username": "newusername", "password": "testpassword123"},
    )
    assert response_login_new.status_code == status.HTTP_200_OK
    token = response_login_new.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test Change Password using JSON body (not query params)
    response_pw = client.put(
        "/api/auth/change-password",
        json={"old_password": "testpassword123", "new_password": "newpassword123"},
        headers=headers,
    )
    assert response_pw.status_code == status.HTTP_200_OK
    assert response_pw.json()["success"] is True

    # Login with new password
    new_login_payload = {
        "username": "newusername",
        "password": "newpassword123",
    }
    response_new_login = client.post("/api/auth/login", json=new_login_payload)
    assert response_new_login.status_code == status.HTTP_200_OK


def test_security_headers(client):
    """Verify security headers on API responses."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "")
    assert "X-Request-ID" in response.headers


def test_unauthorized_access_rejected(client):
    """Verify unauthenticated calls to protected routes return 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
