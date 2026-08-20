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


async def test_registration_grants_initial_wallet_balance(client, backer_headers):
    resp = await client.get("/api/v1/wallet", headers=backer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["balance_minor"] == 10_000_000
    assert body["reserved_minor"] == 0
    assert body["available_minor"] == 10_000_000


async def test_ledger_records_initial_grant(client, backer_headers):
    resp = await client.get("/api/v1/wallet/ledger", headers=backer_headers)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["entry_type"] == "INITIAL_GRANT"
    assert entries[0]["balance_delta_minor"] == 10_000_000
    assert entries[0]["balance_after_minor"] == 10_000_000
    assert entries[0]["reserved_after_minor"] == 0


async def test_placing_back_order_reserves_full_stake(
    client, backer_headers, market_id, selection_ids
):
    place_resp = await _place(
        client, backer_headers, market_id, selection_ids[0], "BACK", "1.10", 500000, "back-reserve"
    )
    assert place_resp.status_code == 201

    wallet_resp = await client.get("/api/v1/wallet", headers=backer_headers)
    body = wallet_resp.json()
    assert body["reserved_minor"] == 500000
    assert body["available_minor"] == 10_000_000 - 500000


async def test_placing_lay_order_reserves_liability_not_stake(
    client, layer_headers, market_id, selection_ids
):
    place_resp = await _place(
        client, layer_headers, market_id, selection_ids[0], "LAY", "1.20", 500000, "lay-reserve"
    )
    assert place_resp.status_code == 201

    wallet_resp = await client.get("/api/v1/wallet", headers=layer_headers)
    body = wallet_resp.json()
    # liability = stake * (price - 1) = 500000 * 0.20 = 100000, not the full stake.
    assert body["reserved_minor"] == 100000
    assert body["available_minor"] == 10_000_000 - 100000


async def test_insufficient_balance_rejects_order_and_leaves_wallet_untouched(
    client, backer_headers, market_id, selection_ids
):
    resp = await _place(
        client,
        backer_headers,
        market_id,
        selection_ids[0],
        "BACK",
        "1.10",
        20_000_000,
        "back-too-big",
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INSUFFICIENT_BALANCE"

    orders_resp = await client.get("/api/v1/orders", headers=backer_headers)
    assert orders_resp.json() == []

    wallet_resp = await client.get("/api/v1/wallet", headers=backer_headers)
    body = wallet_resp.json()
    assert body["reserved_minor"] == 0
    assert body["balance_minor"] == 10_000_000


async def test_cancel_releases_only_the_unmatched_remainder(
    client, backer_headers, layer_headers, market_id, selection_ids
):
    selection_id = selection_ids[0]
    # A small maker only partially fills the upcoming large back order.
    await _place(
        client, layer_headers, market_id, selection_id, "LAY", "1.20", 30000, "lay-partial"
    )

    back_resp = await _place(
        client, backer_headers, market_id, selection_id, "BACK", "1.10", 100000, "back-partial"
    )
    assert back_resp.status_code == 201
    body = back_resp.json()
    assert body["status"] == "PARTIALLY_MATCHED"
    assert body["matched_minor"] == 30000
    assert body["remaining_minor"] == 70000
    order_id = body["id"]

    wallet_before_cancel = (await client.get("/api/v1/wallet", headers=backer_headers)).json()
    assert wallet_before_cancel["reserved_minor"] == 100000  # BACK exposure == full stake

    cancel_resp = await client.delete(f"/api/v1/orders/{order_id}", headers=backer_headers)
    assert cancel_resp.status_code == 200

    wallet_after_cancel = (await client.get("/api/v1/wallet", headers=backer_headers)).json()
    # Only the 70,000 unmatched remainder is released; the 30,000 backing
    # the already-matched Bet stays held until settlement (Step 9).
    assert wallet_after_cancel["reserved_minor"] == 30000
    assert wallet_after_cancel["balance_minor"] == 10_000_000
