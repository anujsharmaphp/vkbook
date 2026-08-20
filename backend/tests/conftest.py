import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.role import Role
from app.models.user import User


@pytest_asyncio.fixture
async def engine():
    # A fresh in-memory SQLite DB per test, isolated by a unique cache name.
    url = f"sqlite+aiosqlite:///file:test_{uuid.uuid4().hex}?mode=memory&cache=shared&uri=true"
    test_engine = create_async_engine(url)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def seed_roles(session_factory):
    async with session_factory() as session:
        session.add(Role(code="user", name="Standard User"))
        session.add(Role(code="admin", name="Administrator"))
        await session.commit()


@pytest_asyncio.fixture
async def client(session_factory, seed_roles):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _register_and_login(
    client, email: str, password: str, display_name: str
) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_headers(client) -> dict[str, str]:
    return await _register_and_login(client, "user@example.com", "user-password1", "Regular User")


@pytest_asyncio.fixture
async def backer_headers(client) -> dict[str, str]:
    return await _register_and_login(client, "backer@example.com", "backer-password1", "Backer")


@pytest_asyncio.fixture
async def layer_headers(client) -> dict[str, str]:
    return await _register_and_login(client, "layer@example.com", "layer-password1", "Layer")


@pytest_asyncio.fixture
async def admin_headers(client, session_factory) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "admin-password1",
            "display_name": "Admin User",
        },
    )
    async with session_factory() as session:
        user_result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = user_result.scalar_one()
        role_result = await session.execute(select(Role).where(Role.code == "admin"))
        admin_role = role_result.scalar_one()
        user.roles.append(admin_role)
        await session.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "admin-password1"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def market_id(client, admin_headers) -> str:
    sport_resp = await client.post(
        "/api/v1/admin/sports", json={"code": "CRICKET", "name": "Cricket"}, headers=admin_headers
    )
    sport_id = sport_resp.json()["id"]

    competition_resp = await client.post(
        "/api/v1/admin/competitions",
        json={"sport_id": sport_id, "name": "Test Matches"},
        headers=admin_headers,
    )
    competition_id = competition_resp.json()["id"]

    event_resp = await client.post(
        "/api/v1/admin/events",
        json={
            "competition_id": competition_id,
            "name": "England vs Pakistan",
            "start_time": "2026-09-01T10:00:00Z",
        },
        headers=admin_headers,
    )
    event_id = event_resp.json()["id"]

    market_type_resp = await client.post(
        "/api/v1/admin/market-types",
        json={
            "code": "MATCH_ODDS",
            "name": "Match Odds",
            "settlement_rule": {"kind": "WINNER_TAKES_ALL"},
        },
        headers=admin_headers,
    )
    market_type_id = market_type_resp.json()["id"]

    market_resp = await client.post(
        "/api/v1/admin/markets",
        json={
            "event_id": event_id,
            "market_type_id": market_type_id,
            "name": "Match Odds",
            "selections": [
                {"name": "England", "display_order": 0},
                {"name": "Pakistan", "display_order": 1},
            ],
        },
        headers=admin_headers,
    )
    assert market_resp.status_code == 201
    return market_resp.json()["id"]


@pytest_asyncio.fixture
async def selection_ids(client, market_id) -> list[str]:
    resp = await client.get(f"/api/v1/markets/{market_id}")
    return [s["id"] for s in resp.json()["selections"]]
