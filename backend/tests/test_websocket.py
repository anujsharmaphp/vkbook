from app.events.publisher import WebSocketEventPublisher
from app.websocket.manager import ConnectionManager


class FakeConnection:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.received: list[dict] = []

    async def send_json(self, data: dict) -> None:
        if self.fail:
            raise RuntimeError("connection closed")
        self.received.append(data)


async def test_broadcast_delivers_only_to_subscribers_of_that_topic():
    manager = ConnectionManager()
    market_conn = FakeConnection()
    other_conn = FakeConnection()
    manager.subscribe("market:m1", market_conn)
    manager.subscribe("market:m2", other_conn)

    await manager.broadcast("market:m1", {"event": "ODDS_UPDATED"})

    assert market_conn.received == [{"event": "ODDS_UPDATED"}]
    assert other_conn.received == []


async def test_broadcast_fans_out_to_multiple_subscribers_of_same_topic():
    manager = ConnectionManager()
    a, b = FakeConnection(), FakeConnection()
    manager.subscribe("market:m1", a)
    manager.subscribe("market:m1", b)

    await manager.broadcast("market:m1", {"event": "MARKET_SUSPENDED"})

    assert a.received == [{"event": "MARKET_SUSPENDED"}]
    assert b.received == [{"event": "MARKET_SUSPENDED"}]


async def test_unsubscribe_stops_further_delivery():
    manager = ConnectionManager()
    conn = FakeConnection()
    manager.subscribe("market:m1", conn)
    manager.unsubscribe("market:m1", conn)

    await manager.broadcast("market:m1", {"event": "MARKET_SUSPENDED"})

    assert conn.received == []


async def test_broadcast_drops_dead_connections_without_raising():
    manager = ConnectionManager()
    dead = FakeConnection(fail=True)
    alive = FakeConnection()
    manager.subscribe("market:m1", dead)
    manager.subscribe("market:m1", alive)

    await manager.broadcast("market:m1", {"event": "ODDS_UPDATED"})

    assert alive.received == [{"event": "ODDS_UPDATED"}]
    # The failing connection was pruned — a second broadcast doesn't retry it.
    await manager.broadcast("market:m1", {"event": "ODDS_UPDATED"})
    assert alive.received == [{"event": "ODDS_UPDATED"}, {"event": "ODDS_UPDATED"}]


async def test_event_publisher_flattens_payload_and_increments_sequence_per_topic():
    manager = ConnectionManager()
    conn = FakeConnection()
    manager.subscribe("market:m1", conn)
    publisher = WebSocketEventPublisher(manager)

    await publisher.publish("market:m1", "ODDS_UPDATED", {"market_id": "m1", "price": "1.12"})
    await publisher.publish("market:m1", "ODDS_UPDATED", {"market_id": "m1", "price": "1.13"})

    assert conn.received[0] == {
        "event": "ODDS_UPDATED",
        "sequence": 1,
        "market_id": "m1",
        "price": "1.12",
    }
    assert conn.received[1]["sequence"] == 2


async def test_event_publisher_sequence_is_independent_per_topic():
    manager = ConnectionManager()
    conn_a, conn_b = FakeConnection(), FakeConnection()
    manager.subscribe("market:a", conn_a)
    manager.subscribe("market:b", conn_b)
    publisher = WebSocketEventPublisher(manager)

    await publisher.publish("market:a", "ODDS_UPDATED", {})
    await publisher.publish("market:a", "ODDS_UPDATED", {})
    await publisher.publish("market:b", "ODDS_UPDATED", {})

    assert conn_a.received[1]["sequence"] == 2
    assert conn_b.received[0]["sequence"] == 1
