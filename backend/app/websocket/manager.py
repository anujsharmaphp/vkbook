import logging
from typing import Protocol

logger = logging.getLogger("app.websocket")


class Sendable(Protocol):
    """Minimal surface ConnectionManager needs from a connection — matches
    both `starlette.websockets.WebSocket` and any test double."""

    async def send_json(self, data: dict) -> None: ...


class ConnectionManager:
    """Tracks which connections are subscribed to which topic
    (`market:{id}`, `event:{id}`, `user:{id}`) and fans out messages to
    them. One process-wide instance today; the WebSocket route handlers are
    its only clients, so swapping this for a Redis-Streams-backed fanout
    later (to support multiple backend instances) only touches this file
    and app/events/publisher.py.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, set[Sendable]] = {}

    def subscribe(self, topic: str, connection: Sendable) -> None:
        self._subscribers.setdefault(topic, set()).add(connection)

    def unsubscribe(self, topic: str, connection: Sendable) -> None:
        subscribers = self._subscribers.get(topic)
        if subscribers is None:
            return
        subscribers.discard(connection)
        if not subscribers:
            self._subscribers.pop(topic, None)

    async def broadcast(self, topic: str, message: dict) -> None:
        dead: list[Sendable] = []
        for connection in list(self._subscribers.get(topic, ())):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.unsubscribe(topic, connection)


connection_manager = ConnectionManager()
