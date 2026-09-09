async def _register(client, email, role="club_admin", password="password123", name="Admin"):
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name, "role": role},
    )
    body = response.json()
    return body["access_token"], body["user"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


async def test_club_admin_can_create_club(client):
    token, _ = await _register(client, "owner@nu.edu.kz")

    response = await client.post(
        "/clubs",
        json={"name": "Chess Club", "description": "We play chess"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Chess Club"
    assert body["description"] == "We play chess"


async def test_student_cannot_create_club(client):
    token, _ = await _register(client, "student@nu.edu.kz", role="student")

    response = await client.post(
        "/clubs",
        json={"name": "Chess Club", "description": "We play chess"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


async def test_create_club_requires_authentication(client):
    response = await client.post("/clubs", json={"name": "Chess Club", "description": ""})

    assert response.status_code == 401


async def test_list_clubs(client):
    token, _ = await _register(client, "owner2@nu.edu.kz")
    await client.post("/clubs", json={"name": "Debate Club", "description": ""}, headers=_auth_headers(token))

    response = await client.get("/clubs")

    assert response.status_code == 200
    names = [club["name"] for club in response.json()]
    assert "Debate Club" in names


async def test_get_club_not_found(client):
    response = await client.get("/clubs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_owner_can_update_club(client):
    token, _ = await _register(client, "owner3@nu.edu.kz")
    create_response = await client.post(
        "/clubs", json={"name": "Old Name", "description": "Old"}, headers=_auth_headers(token)
    )
    club_id = create_response.json()["id"]

    response = await client.patch(
        f"/clubs/{club_id}",
        json={"name": "New Name"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["description"] == "Old"


async def test_non_owner_cannot_update_club(client):
    owner_token, _ = await _register(client, "owner4@nu.edu.kz")
    other_token, _ = await _register(client, "other4@nu.edu.kz")
    create_response = await client.post(
        "/clubs", json={"name": "Robotics", "description": ""}, headers=_auth_headers(owner_token)
    )
    club_id = create_response.json()["id"]

    response = await client.patch(
        f"/clubs/{club_id}",
        json={"name": "Hijacked"},
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 403
