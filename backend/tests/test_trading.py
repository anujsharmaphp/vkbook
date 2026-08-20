async def _place(client, headers, market_id, selection_id, side, price, stake_minor, idem):
    return await client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "selection_id": selection_id,
            "side": side,
            "price": price,
            "stake_minor": stake_minor,
            "idempotency_key": idem,
        },
        headers=headers,
    )


async def test_no_match_when_lay_price_below_back_price(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]

    lay_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.10", 50000, "lay-1"
    )
    assert lay_resp.status_code == 201
    assert lay_resp.json()["status"] == "OPEN"

    back_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.12", 50000, "back-1"
    )
    assert back_resp.status_code == 201
    body = back_resp.json()
    assert body["status"] == "OPEN"
    assert body["matched_minor"] == 0
    assert body["remaining_minor"] == 50000


async def test_exact_price_match_fills_fully(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]

    lay_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.13", 50000, "lay-2"
    )
    assert lay_resp.status_code == 201

    back_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.13", 50000, "back-2"
    )
    assert back_resp.status_code == 201
    body = back_resp.json()
    assert body["status"] == "MATCHED"
    assert body["matched_minor"] == 50000
    assert body["remaining_minor"] == 0


async def test_taker_gets_price_improvement_and_priority_by_best_price(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    """Two resting LAY makers (1.13 and 1.15) with a BACK taker at 1.12.

    Both are eligible (lay.price >= back.price). The taker must be filled
    against the *highest* eligible lay price first (1.15, best for the
    backer) before falling back to 1.13, and every fill executes at the
    maker's own price — never the taker's limit.
    """
    selection_id = selection_ids[0]

    x_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.13", 50000, "lay-x"
    )
    y_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.15", 30000, "lay-y"
    )
    assert x_resp.status_code == 201
    assert y_resp.status_code == 201

    back_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.12", 100000, "back-3"
    )
    assert back_resp.status_code == 201
    body = back_resp.json()
    assert body["status"] == "PARTIALLY_MATCHED"
    assert body["matched_minor"] == 80000
    assert body["remaining_minor"] == 20000

    bets_resp = await client.get("/api/v1/bets", headers=backer_headers)
    bets = sorted(bets_resp.json(), key=lambda b: b["price"], reverse=True)
    assert len(bets) == 2
    assert bets[0]["price"] == "1.15"
    assert bets[0]["stake_minor"] == 30000
    assert bets[1]["price"] == "1.13"
    assert bets[1]["stake_minor"] == 50000


async def test_shared_liquidity_never_over_consumed_across_two_takers(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    """Section 22: two takers hitting the same ₹1000 resting maker must
    never collectively consume more than ₹1000, regardless of order."""
    selection_id = selection_ids[0]

    maker_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.20", 100000, "lay-shared"
    )
    assert maker_resp.status_code == 201

    first_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 80000, "back-shared-1"
    )
    assert first_resp.status_code == 201
    first = first_resp.json()
    assert first["status"] == "MATCHED"
    assert first["matched_minor"] == 80000

    second_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 70000, "back-shared-2"
    )
    assert second_resp.status_code == 201
    second = second_resp.json()
    # Only the 20,000 left on the maker is available — never 70,000.
    assert second["status"] == "PARTIALLY_MATCHED"
    assert second["matched_minor"] == 20000
    assert second["remaining_minor"] == 50000

    order_book_resp = await client.get(f"/api/v1/markets/{market_id}/order-book")
    selection_book = next(
        s for s in order_book_resp.json()["selections"] if s["selection_id"] == selection_id
    )
    # Displayed "back" prices are sourced from resting LAY orders (see
    # MatchingService.get_order_book) — the maker was a LAY order, so its
    # exhausted liquidity shows up here, at 0: 80,000 + 20,000 == 100,000.
    back_total = sum(level["available_size_minor"] for level in selection_book["back"])
    assert back_total == 0
    # The second taker's unmatched remainder (50,000) is now a resting BACK
    # order, which displays under "lay" (sourced from resting BACK orders).
    lay_total = sum(level["available_size_minor"] for level in selection_book["lay"])
    assert lay_total == 50000


async def test_liability_minor_computed_per_side(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]
    await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.20", 100000, "lay-liab"
    )
    await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 50000, "back-liab"
    )

    backer_bets = (await client.get("/api/v1/bets", headers=backer_headers)).json()
    layer_bets = (await client.get("/api/v1/bets", headers=layer_headers)).json()

    back_bet = next(b for b in backer_bets if b["side"] == "BACK")
    lay_bet = next(b for b in layer_bets if b["side"] == "LAY")

    assert back_bet["stake_minor"] == 50000
    assert back_bet["liability_minor"] == 50000  # backer risks their stake

    assert lay_bet["stake_minor"] == 50000
    # liability = stake * (price - 1) = 50000 * 0.20 = 10000
    assert lay_bet["liability_minor"] == 10000


async def test_idempotency_key_replay_returns_same_order(
    client, backer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]
    first = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 10000, "dup-key"
    )
    second = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 10000, "dup-key"
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    orders_resp = await client.get("/api/v1/orders", headers=backer_headers)
    assert len(orders_resp.json()) == 1


async def test_cancel_order_removes_it_from_matching(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]
    back_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 40000, "back-cancel"
    )
    order_id = back_resp.json()["id"]

    cancel_resp = await client.delete(f"/api/v1/orders/{order_id}", headers=backer_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # A generous lay order arrives after cancellation — must not match the
    # now-cancelled back order.
    lay_resp = await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.50", 40000, "lay-after-cancel"
    )
    assert lay_resp.status_code == 201
    assert lay_resp.json()["status"] == "OPEN"
    assert lay_resp.json()["matched_minor"] == 0

    double_cancel_resp = await client.delete(f"/api/v1/orders/{order_id}", headers=backer_headers)
    assert double_cancel_resp.status_code == 409
    assert double_cancel_resp.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"


async def test_cannot_place_order_on_suspended_market(
    client, admin_headers, backer_headers, market_id, selection_ids
):
    suspend_resp = await client.post(
        f"/api/v1/admin/markets/{market_id}/suspend", headers=admin_headers
    )
    assert suspend_resp.status_code == 200

    resp = await _place(
        client, backer_headers, market_id, selection_ids[0], "BACK", "1.10", 10000, "back-suspended"
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "MARKET_NOT_OPEN"


async def test_placing_order_requires_authentication(client, market_id, selection_ids):
    resp = await _place(client, {}, market_id, selection_ids[0], "BACK", "1.10", 10000, "no-auth")
    assert resp.status_code == 401
