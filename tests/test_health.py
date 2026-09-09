from httpx import ASGITransport, AsyncClient

from app.db import get_db, get_redis


class _FakeSession:
    async def execute(self, *_args, **_kwargs):
        return None


class _FakeRedis:
    async def ping(self):
        return True


async def test_health_ok(app):
    app.dependency_overrides[get_db] = lambda: _FakeSession()
    app.dependency_overrides[get_redis] = lambda: _FakeRedis()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True, "redis": True}
