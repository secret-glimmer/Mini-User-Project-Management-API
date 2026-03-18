import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_user(client: AsyncClient, **overrides) -> dict:
    payload = {"name": "Alice", "email": "alice@example.com", **overrides}
    resp = await client.post("/users", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def test_create_project(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.post(
        "/projects",
        json={"title": "My Project", "description": "Desc", "owner_id": user["id"]},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My Project"
    assert data["description"] == "Desc"
    assert data["owner_id"] == user["id"]
    assert "id" in data
    assert "created_at" in data


async def test_create_project_nonexistent_owner(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        "/projects",
        json={"title": "Orphan", "owner_id": fake_id},
    )
    assert resp.status_code == 404
    assert "detail" in resp.json()


async def test_create_project_missing_title(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.post("/projects", json={"owner_id": user["id"]})
    assert resp.status_code == 422


async def test_create_project_whitespace_only_title(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.post(
        "/projects", json={"title": "   ", "owner_id": user["id"]}
    )
    assert resp.status_code == 422


async def test_create_project_strips_title_whitespace(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.post(
        "/projects", json={"title": "  My Project  ", "owner_id": user["id"]}
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "My Project"


async def test_create_project_null_description(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.post(
        "/projects",
        json={"title": "NoDesc", "description": None, "owner_id": user["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


async def test_create_project_whitespace_description_becomes_null(
    client: AsyncClient,
):
    user = await _create_user(client)
    resp = await client.post(
        "/projects",
        json={"title": "Proj", "description": "   ", "owner_id": user["id"]},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


async def test_create_project_missing_owner_id(client: AsyncClient):
    resp = await client.post("/projects", json={"title": "NoOwner"})
    assert resp.status_code == 422


async def test_create_project_invalid_owner_uuid(client: AsyncClient):
    resp = await client.post(
        "/projects", json={"title": "Bad", "owner_id": "not-a-uuid"}
    )
    assert resp.status_code == 422


async def test_get_project(client: AsyncClient):
    user = await _create_user(client)
    created = await client.post(
        "/projects",
        json={"title": "P1", "owner_id": user["id"]},
    )
    project_id = created.json()["id"]

    resp = await client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "P1"


async def test_get_project_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/projects/{fake_id}")
    assert resp.status_code == 404


async def test_get_project_invalid_uuid(client: AsyncClient):
    resp = await client.get("/projects/not-a-uuid")
    assert resp.status_code == 422


async def test_list_user_projects(client: AsyncClient):
    user = await _create_user(client)
    uid = user["id"]
    for i in range(3):
        await client.post(
            "/projects",
            json={"title": f"Project {i}", "owner_id": uid},
        )

    resp = await client.get(f"/users/{uid}/projects")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_list_user_projects_empty(client: AsyncClient):
    user = await _create_user(client)
    resp = await client.get(f"/users/{user['id']}/projects")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_user_projects_user_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/users/{fake_id}/projects")
    assert resp.status_code == 404


async def test_list_user_projects_deterministic_order(client: AsyncClient):
    user = await _create_user(client)
    uid = user["id"]
    ids = []
    for i in range(3):
        r = await client.post(
            "/projects", json={"title": f"P{i}", "owner_id": uid}
        )
        ids.append(r.json()["id"])

    resp = await client.get(f"/users/{uid}/projects")
    returned_ids = [p["id"] for p in resp.json()]
    assert returned_ids == ids
