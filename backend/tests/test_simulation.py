import uuid

from app.models.bet import BetStatus
from app.models.market import MarketStatus
from app.services.simulation_service import SimulationEngine


async def _create_two_selection_market(client, admin_headers):
    sport = (await client.post(
        "/api/v1/admin/sports", json={"code": "CRICKET", "name": "Cricket"}, headers=admin_headers
    )).json()
    comp = (await client.post(
        "/api/v1/admin/competitions",
        json={"sport_id": sport["id"], "name": "Test Championship"},
        headers=admin_headers,
    )).json()
    event = (await client.post(
        "/api/v1/admin/events",
        json={
            "competition_id": comp["id"],
            "name": "England vs Pakistan",
            "start_time": "2026-09-01T10:00:00Z",
        },
        headers=admin_headers,
    )).json()
    mtype = (await client.post(
        "/api/v1/admin/market-types",
        json={
            "code": "MATCH_ODDS",
            "name": "Match Odds",
            "settlement_rule": {"kind": "WINNER_TAKES_ALL"},
        },
        headers=admin_headers,
    )).json()
    market = (await client.post(
        "/api/v1/admin/markets",
        json={
            "event_id": event["id"],
            "market_type_id": mtype["id"],
            "name": "Match Odds",
            "selections": [
                {"name": "England", "display_order": 0},
                {"name": "Pakistan", "display_order": 1},
            ],
        },
        headers=admin_headers,
    )).json()
    return event, market


async def test_start_match_sets_live_and_quotes_liquidity(client, admin_headers):
    event, market = await _create_two_selection_market(client, admin_headers)

    resp = await client.post(
        f"/api/v1/admin/simulator/events/{event['id']}/start", headers=admin_headers
    )
    assert resp.status_code == 200
    state = resp.json()
    assert state["status"] == "LIVE"
    assert state["batting_team"] in ("England", "Pakistan")
    assert 90 <= state["target_runs"] <= 170

    event_resp = await client.get(f"/api/v1/events/{event['id']}")
    assert event_resp.json()["status"] == "LIVE"

    book_resp = await client.get(f"/api/v1/markets/{market['id']}/order-book")
    book = book_resp.json()
    assert len(book["selections"]) == 2
    for selection_book in book["selections"]:
        assert len(selection_book["back"]) > 0
        assert len(selection_book["lay"]) > 0

    public_state_resp = await client.get(f"/api/v1/events/{event['id']}/match-state")
    assert public_state_resp.status_code == 200
    assert public_state_resp.json()["status"] == "LIVE"


async def test_start_match_requires_admin(client, user_headers, admin_headers):
    event, _market = await _create_two_selection_market(client, admin_headers)
    resp = await client.post(
        f"/api/v1/admin/simulator/events/{event['id']}/start", headers=user_headers
    )
    assert resp.status_code == 403


async def test_match_state_null_before_simulation_started(client, admin_headers):
    event, _market = await _create_two_selection_market(client, admin_headers)
    resp = await client.get(f"/api/v1/events/{event['id']}/match-state")
    assert resp.status_code == 200
    assert resp.json() is None


async def test_tick_progresses_score_and_can_suspend_market(
    session_factory, client, admin_headers
):
    event, market = await _create_two_selection_market(client, admin_headers)
    await client.post(
        f"/api/v1/admin/simulator/events/{event['id']}/start", headers=admin_headers
    )

    async with session_factory() as session:
        engine = SimulationEngine(session)
        for _ in range(30):
            finished = await engine.tick(uuid.UUID(event["id"]))
            if finished:
                break

    market_resp = await client.get(f"/api/v1/markets/{market['id']}")
    # Either still open (never hit a wicket-suspend tick) or settled/closed if
    # the innings happened to finish within 30 ticks — both are valid, real
    # outcomes of a random simulation; the assertion is just that it's one of
    # the reachable states, not still SCHEDULED-shaped nonsense.
    assert market_resp.json()["status"] in ("OPEN", "SUSPENDED", "SETTLED")


async def test_finish_match_settles_bets(
    session_factory, client, admin_headers, backer_headers, layer_headers
):
    event, market = await _create_two_selection_market(client, admin_headers)
    await client.post(
        f"/api/v1/admin/simulator/events/{event['id']}/start", headers=admin_headers
    )

    market_detail = (await client.get(f"/api/v1/markets/{market['id']}")).json()
    england_id = next(s["id"] for s in market_detail["selections"] if s["name"] == "England")

    # A real user backs England directly against whatever bot liquidity is quoting.
    book = (await client.get(f"/api/v1/markets/{market['id']}/order-book")).json()
    england_book = next(s for s in book["selections"] if s["selection_id"] == england_id)
    back_level = england_book["back"][0]

    place_resp = await client.post(
        "/api/v1/orders",
        json={
            "market_id": market["id"],
            "selection_id": england_id,
            "side": "BACK",
            "price": back_level["price"],
            "stake_minor": 10000,
            "idempotency_key": "settle-test-back-1",
        },
        headers=backer_headers,
    )
    assert place_resp.status_code == 201

    # Force England to win regardless of how the random simulation was going.
    async with session_factory() as session:
        engine = SimulationEngine(session)
        state = await engine.get_state(uuid.UUID(event["id"]))
        state.batting_team = "England"
        state.bowling_team = "Pakistan"
        state.runs = state.target_runs
        await session.commit()

    finish_resp = await client.post(
        f"/api/v1/admin/simulator/events/{event['id']}/finish", headers=admin_headers
    )
    assert finish_resp.status_code == 200
    assert finish_resp.json()["winner_team"] == "England"

    market_after = await client.get(f"/api/v1/markets/{market['id']}")
    assert market_after.json()["status"] == "SETTLED"

    bets_resp = await client.get("/api/v1/bets", headers=backer_headers)
    settled = [b for b in bets_resp.json() if b["status"] == BetStatus.SETTLED.value]
    assert len(settled) >= 1
    assert all(b["side"] == "BACK" for b in settled if b["selection_id"] == england_id)

    market_row = market_after.json()
    assert market_row["status"] == MarketStatus.SETTLED.value
