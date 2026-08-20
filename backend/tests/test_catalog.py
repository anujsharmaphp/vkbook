import uuid

import pytest

from app.core.errors import ConflictError


async def test_create_full_catalog_hierarchy_and_public_reads(client, market_id):
    market_resp = await client.get(f"/api/v1/markets/{market_id}")
    assert market_resp.status_code == 200
    body = market_resp.json()
    assert body["status"] == "OPEN"
    assert body["version"] == 1
    assert [s["name"] for s in body["selections"]] == ["England", "Pakistan"]

    sports_resp = await client.get("/api/v1/sports")
    assert sports_resp.status_code == 200
    assert any(s["code"] == "CRICKET" for s in sports_resp.json())


async def test_event_detail_includes_markets(client, market_id):
    events_resp = await client.get("/api/v1/events")
    assert events_resp.status_code == 200
    assert len(events_resp.json()) == 1
    event_id = events_resp.json()[0]["id"]

    detail_resp = await client.get(f"/api/v1/events/{event_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["name"] == "England vs Pakistan"
    assert len(detail["markets"]) == 1
    assert detail["markets"][0]["id"] == market_id


async def test_admin_endpoints_require_admin_role(client, user_headers):
    resp = await client.post(
        "/api/v1/admin/sports", json={"code": "FOOTBALL", "name": "Football"}, headers=user_headers
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_admin_endpoints_require_authentication(client):
    resp = await client.post("/api/v1/admin/sports", json={"code": "TENNIS", "name": "Tennis"})
    assert resp.status_code == 401


async def test_duplicate_sport_code_rejected(client, admin_headers):
    await client.post(
        "/api/v1/admin/sports", json={"code": "GOLF", "name": "Golf"}, headers=admin_headers
    )
    dup = await client.post(
        "/api/v1/admin/sports", json={"code": "GOLF", "name": "Golf Again"}, headers=admin_headers
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "SPORT_CODE_TAKEN"


async def test_market_requires_at_least_one_selection(client, admin_headers):
    sport_resp = await client.post(
        "/api/v1/admin/sports", json={"code": "TENNIS", "name": "Tennis"}, headers=admin_headers
    )
    competition_resp = await client.post(
        "/api/v1/admin/competitions",
        json={"sport_id": sport_resp.json()["id"], "name": "ATP"},
        headers=admin_headers,
    )
    event_resp = await client.post(
        "/api/v1/admin/events",
        json={
            "competition_id": competition_resp.json()["id"],
            "name": "Final",
            "start_time": "2026-09-01T10:00:00Z",
        },
        headers=admin_headers,
    )
    market_type_resp = await client.post(
        "/api/v1/admin/market-types",
        json={"code": "WINNER", "name": "Winner", "settlement_rule": {"kind": "WINNER_TAKES_ALL"}},
        headers=admin_headers,
    )
    resp = await client.post(
        "/api/v1/admin/markets",
        json={
            "event_id": event_resp.json()["id"],
            "market_type_id": market_type_resp.json()["id"],
            "name": "Winner",
            "selections": [],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 422


async def test_market_suspend_reopen_close_state_machine(client, admin_headers, market_id):
    suspend_url = f"/api/v1/admin/markets/{market_id}/suspend"
    reopen_url = f"/api/v1/admin/markets/{market_id}/reopen"
    close_url = f"/api/v1/admin/markets/{market_id}/close"

    suspend_resp = await client.post(suspend_url, headers=admin_headers)
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["status"] == "SUSPENDED"
    assert suspend_resp.json()["version"] == 2

    invalid_resp = await client.post(suspend_url, headers=admin_headers)
    assert invalid_resp.status_code == 409
    assert invalid_resp.json()["error"]["code"] == "INVALID_MARKET_TRANSITION"

    reopen_resp = await client.post(reopen_url, headers=admin_headers)
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "OPEN"
    assert reopen_resp.json()["version"] == 3

    close_resp = await client.post(close_url, headers=admin_headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "CLOSED"

    reopen_after_close_resp = await client.post(reopen_url, headers=admin_headers)
    assert reopen_after_close_resp.status_code == 409
    assert reopen_after_close_resp.json()["error"]["code"] == "INVALID_MARKET_TRANSITION"


async def test_concurrent_market_transition_raises_version_conflict(session_factory, market_id):
    from app.services.market_service import MarketService

    async with session_factory() as session_a, session_factory() as session_b:
        service_a = MarketService(session_a)
        service_b = MarketService(session_b)

        market_a = await service_a.get_market(uuid.UUID(market_id))
        market_b = await service_b.get_market(uuid.UUID(market_id))
        assert market_a.version == market_b.version == 1

        # A suspends and commits first — the DB row is now version 2.
        await service_a.suspend_market(market_a.id)

        # B is still holding the version-1 view it loaded before A committed.
        # Its UPDATE ... WHERE version = 1 matches zero rows.
        with pytest.raises(ConflictError) as exc_info:
            await service_b.suspend_market(market_b.id)
        assert exc_info.value.code == "MARKET_VERSION_CONFLICT"
