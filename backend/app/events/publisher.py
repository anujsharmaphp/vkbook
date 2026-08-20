import json
import logging
from typing import Any, Protocol

from app.websocket.manager import ConnectionManager, connection_manager

logger = logging.getLogger("app.events")


class EventPublisher(Protocol):
    async def publish(self, topic: str, event_type: str, payload: dict[str, Any]) -> None: ...


class NullEventPublisher:
    """Logs domain events instead of fanning them out anywhere. Useful for
    isolated unit tests that want to assert on published events without a
    live WebSocket connection."""

    async def publish(self, topic: str, event_type: str, payload: dict[str, Any]) -> None:
        record = {"topic": topic, "event_type": event_type, "payload": payload}
        logger.info(json.dumps(record, default=str))


class WebSocketEventPublisher:
    """Fans domain events out to WebSocket clients subscribed to their
    topic, via ConnectionManager. Payload fields are flattened alongside
    `event`/`sequence` to match docs/architecture.md Section 7's wire shape.
    `sequence` is per-topic and monotonically increasing (Section 19), so
    clients can detect gaps and trigger a REST resync.

    This is the in-process, single-instance fanout. A production,
    horizontally-scaled deployment replaces this with a publisher that
    XADDs to Redis Streams and a separate consumer per gateway instance that
    reads the stream and calls the same ConnectionManager.broadcast — no
    caller of get_event_publisher() needs to change.
    """

    def __init__(self, manager: ConnectionManager = connection_manager) -> None:
        self._manager = manager
        self._sequences: dict[str, int] = {}

    async def publish(self, topic: str, event_type: str, payload: dict[str, Any]) -> None:
        self._sequences[topic] = self._sequences.get(topic, 0) + 1
        message = {"event": event_type, "sequence": self._sequences[topic], **payload}
        await self._manager.broadcast(topic, message)


_publisher: EventPublisher = WebSocketEventPublisher()


def get_event_publisher() -> EventPublisher:
    return _publisher
