from datetime import datetime, timedelta, timezone


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email, role="club_admin", password="password123", name="Admin"):
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name, "role": role},
    )
    body = response.json()
    return body["access_token"], body["user"]


async def _create_club(client, token, name="Chess Club"):
    response = await client.post("/clubs", json={"name": name, "description": ""}, headers=_auth_headers(token))
    return response.json()["id"]


def _event_payload(club_id, **overrides):
    start = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        "club_id": club_id,
        "title": "Weekly Meetup",
        "description": "Casual games",
        "location": "Room 101",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "capacity": 20,
    }
    payload.update(overrides)
    return payload


async def test_create_event_success(client):
    token, _ = await _register(client, "clubadmin1@nu.edu.kz")
    club_id = await _create_club(client, token)

    response = await client.post("/events", json=_event_payload(club_id), headers=_auth_headers(token))

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Weekly Meetup"
    assert body["registration_status"] == "not_open"
    assert body["capacity"] == 20


async def test_create_event_forbidden_for_non_owner(client):
    owner_token, _ = await _register(client, "clubadmin2@nu.edu.kz")
    other_token, _ = await _register(client, "clubadmin3@nu.edu.kz")
    club_id = await _create_club(client, owner_token)

    response = await client.post("/events", json=_event_payload(club_id), headers=_auth_headers(other_token))

    assert response.status_code == 403


async def test_create_event_requires_club_admin_role(client):
    student_token, _ = await _register(client, "student1@nu.edu.kz", role="student")

    response = await client.post(
        "/events",
        json=_event_payload("00000000-0000-0000-0000-000000000000"),
        headers=_auth_headers(student_token),
    )

    assert response.status_code == 403


async def test_create_event_rejects_end_before_start(client):
    token, _ = await _register(client, "clubadmin4@nu.edu.kz")
    club_id = await _create_club(client, token)
    start = datetime.now(timezone.utc) + timedelta(days=1)

    response = await client.post(
        "/events",
        json=_event_payload(club_id, start_time=start.isoformat(), end_time=(start - timedelta(hours=1)).isoformat()),
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


async def test_open_and_close_registration_flow(client):
    token, _ = await _register(client, "clubadmin5@nu.edu.kz")
    club_id = await _create_club(client, token)
    create_response = await client.post("/events", json=_event_payload(club_id), headers=_auth_headers(token))
    event_id = create_response.json()["id"]

    open_response = await client.post(f"/events/{event_id}/open", headers=_auth_headers(token))
    assert open_response.status_code == 200
    assert open_response.json()["registration_status"] == "open"

    reopen_response = await client.post(f"/events/{event_id}/open", headers=_auth_headers(token))
    assert reopen_response.status_code == 400

    close_response = await client.post(f"/events/{event_id}/close", headers=_auth_headers(token))
    assert close_response.status_code == 200
    assert close_response.json()["registration_status"] == "closed"

    reclose_response = await client.post(f"/events/{event_id}/close", headers=_auth_headers(token))
    assert reclose_response.status_code == 400


async def test_close_before_open_rejected(client):
    token, _ = await _register(client, "clubadmin6@nu.edu.kz")
    club_id = await _create_club(client, token)
    create_response = await client.post("/events", json=_event_payload(club_id), headers=_auth_headers(token))
    event_id = create_response.json()["id"]

    response = await client.post(f"/events/{event_id}/close", headers=_auth_headers(token))

    assert response.status_code == 400


async def test_get_event_not_found(client):
    response = await client.get("/events/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_list_events_filters_by_club_and_status(client):
    token, _ = await _register(client, "clubadmin7@nu.edu.kz")
    club_a = await _create_club(client, token, name="Club A")
    club_b = await _create_club(client, token, name="Club B")

    event_a = (
        await client.post("/events", json=_event_payload(club_a, title="Event A"), headers=_auth_headers(token))
    ).json()
    await client.post("/events", json=_event_payload(club_b, title="Event B"), headers=_auth_headers(token))
    await client.post(f"/events/{event_a['id']}/open", headers=_auth_headers(token))

    by_club = await client.get("/events", params={"club_id": club_a})
    assert {event["title"] for event in by_club.json()} == {"Event A"}

    by_status = await client.get("/events", params={"status": "open"})
    assert {event["title"] for event in by_status.json()} == {"Event A"}

    by_status_not_open = await client.get("/events", params={"status": "not_open"})
    assert {event["title"] for event in by_status_not_open.json()} == {"Event B"}


async def test_list_events_filters_by_date_range(client):
    token, _ = await _register(client, "clubadmin8@nu.edu.kz")
    club_id = await _create_club(client, token)

    near = datetime.now(timezone.utc) + timedelta(days=1)
    far = datetime.now(timezone.utc) + timedelta(days=30)
    await client.post(
        "/events",
        json=_event_payload(club_id, title="Near Event", start_time=near.isoformat(), end_time=(near + timedelta(hours=1)).isoformat()),
        headers=_auth_headers(token),
    )
    await client.post(
        "/events",
        json=_event_payload(club_id, title="Far Event", start_time=far.isoformat(), end_time=(far + timedelta(hours=1)).isoformat()),
        headers=_auth_headers(token),
    )

    response = await client.get(
        "/events",
        params={
            "start_date": near.date().isoformat(),
            "end_date": near.date().isoformat(),
        },
    )

    assert {event["title"] for event in response.json()} == {"Near Event"}


async def test_owner_can_update_event(client):
    token, _ = await _register(client, "clubadmin9@nu.edu.kz")
    club_id = await _create_club(client, token)
    create_response = await client.post("/events", json=_event_payload(club_id), headers=_auth_headers(token))
    event_id = create_response.json()["id"]

    response = await client.patch(
        f"/events/{event_id}",
        json={"title": "Updated Title", "capacity": 5},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Title"
    assert body["capacity"] == 5
