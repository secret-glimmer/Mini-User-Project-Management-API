import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_user(client: AsyncClient, **overrides) -> dict:
    payload = {"name": "Alice", "email": "alice@example.com", **overrides}
    resp = await client.post("/users", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def test_create_user(client: AsyncClient):
    data = await _create_user(client)
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data
    uuid.UUID(data["id"])


async def test_create_user_duplicate_email(client: AsyncClient):
    await _create_user(client)
    resp = await client.post(
        "/users", json={"name": "Bob", "email": "alice@example.com"}
    )
    assert resp.status_code == 409
    assert "detail" in resp.json()


async def test_create_user_email_case_insensitive(client: AsyncClient):
    await _create_user(client, email="Alice@Example.COM")
    resp = await client.post(
        "/users", json={"name": "Bob", "email": "alice@example.com"}
    )
    assert resp.status_code == 409


async def test_create_user_invalid_email(client: AsyncClient):
    resp = await client.post("/users", json={"name": "X", "email": "not-an-email"})
    assert resp.status_code == 422


async def test_create_user_empty_name(client: AsyncClient):
    resp = await client.post("/users", json={"name": "", "email": "a@b.com"})
    assert resp.status_code == 422


async def test_create_user_whitespace_only_name(client: AsyncClient):
    resp = await client.post("/users", json={"name": "   ", "email": "a@b.com"})
    assert resp.status_code == 422


async def test_create_user_strips_name_whitespace(client: AsyncClient):
    data = await _create_user(client, name="  Alice  ")
    assert data["name"] == "Alice"


async def test_create_user_missing_fields(client: AsyncClient):
    resp = await client.post("/users", json={})
    assert resp.status_code == 422

    resp = await client.post("/users", json={"name": "X"})
    assert resp.status_code == 422


async def test_get_user(client: AsyncClient):
    created = await _create_user(client)
    resp = await client.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_user_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/users/{fake_id}")
    assert resp.status_code == 404
    assert "detail" in resp.json()


async def test_get_user_invalid_uuid(client: AsyncClient):
    resp = await client.get("/users/not-a-uuid")
    assert resp.status_code == 422


async def test_list_users_empty(client: AsyncClient):
    resp = await client.get("/users")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_users_pagination(client: AsyncClient):
    for i in range(5):
        await _create_user(client, name=f"User{i}", email=f"user{i}@test.com")

    resp = await client.get("/users", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/users", params={"limit": 10, "offset": 3})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_users_offset_beyond_total(client: AsyncClient):
    await _create_user(client)
    resp = await client.get("/users", params={"limit": 10, "offset": 999})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_users_invalid_limit(client: AsyncClient):
    resp = await client.get("/users", params={"limit": 0})
    assert resp.status_code == 422

    resp = await client.get("/users", params={"limit": 999})
    assert resp.status_code == 422


async def test_list_users_deterministic_order(client: AsyncClient):
    ids = []
    for i in range(3):
        u = await _create_user(client, name=f"User{i}", email=f"u{i}@test.com")
        ids.append(u["id"])

    resp = await client.get("/users", params={"limit": 10})
    returned_ids = [u["id"] for u in resp.json()]
    assert returned_ids == ids


async def test_delete_user(client: AsyncClient):
    created = await _create_user(client)
    resp = await client.delete(f"/users/{created['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/users/{created['id']}")
    assert resp.status_code == 404


async def test_delete_user_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.delete(f"/users/{fake_id}")
    assert resp.status_code == 404


async def test_delete_user_cascades_projects(client: AsyncClient):
    user = await _create_user(client)
    uid = user["id"]

    for i in range(3):
        resp = await client.post(
            "/projects",
            json={"title": f"Proj{i}", "owner_id": uid},
        )
        assert resp.status_code == 201

    resp = await client.get(f"/users/{uid}/projects")
    assert len(resp.json()) == 3

    resp = await client.delete(f"/users/{uid}")
    assert resp.status_code == 204

    resp = await client.get(f"/users/{uid}/projects")
    assert resp.status_code == 404


async def test_delete_user_idempotent_404(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.delete(f"/users/{user['id']}")
    assert resp.status_code == 204

    resp = await client.delete(f"/users/{user['id']}")
    assert resp.status_code == 404
