import pytest
from fastapi import HTTPException

from app.users.dependencies import require_role
from app.users.models import User, UserRole


async def _register(client, email="alice@nu.edu.kz", password="password123", name="Alice", role="student"):
    return await client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name, "role": role},
    )


async def test_register_creates_user_and_returns_token(client):
    response = await _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "alice@nu.edu.kz"
    assert body["user"]["role"] == "student"
    assert "password" not in body["user"]


async def test_register_duplicate_email_returns_409(client):
    await _register(client)
    response = await _register(client)

    assert response.status_code == 409


async def test_login_success(client):
    await _register(client, email="bob@nu.edu.kz", password="password123", role="club_admin")

    response = await client.post("/auth/login", json={"email": "bob@nu.edu.kz", "password": "password123"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "club_admin"


async def test_login_wrong_password_returns_401(client):
    await _register(client, email="carol@nu.edu.kz", password="password123")

    response = await client.post("/auth/login", json={"email": "carol@nu.edu.kz", "password": "wrongpass"})

    assert response.status_code == 401


async def test_login_unknown_email_returns_401(client):
    response = await client.post("/auth/login", json={"email": "nobody@nu.edu.kz", "password": "whatever"})

    assert response.status_code == 401


async def test_me_requires_authentication(client):
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_me_returns_current_user(client):
    register_response = await _register(client, email="dave@nu.edu.kz", password="password123")
    token = register_response.json()["access_token"]

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "dave@nu.edu.kz"


async def test_me_rejects_garbage_token(client):
    response = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def _fake_user(role: UserRole) -> User:
    return User(id=None, email="x@x.com", password_hash="h", name="X", role=role)


async def test_require_role_allows_matching_role():
    check = require_role(UserRole.CLUB_ADMIN)
    user = _fake_user(UserRole.CLUB_ADMIN)

    assert await check(user) is user


async def test_require_role_rejects_other_role():
    check = require_role(UserRole.CLUB_ADMIN)
    user = _fake_user(UserRole.STUDENT)

    with pytest.raises(HTTPException) as exc_info:
        await check(user)

    assert exc_info.value.status_code == 403
