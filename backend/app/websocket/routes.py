import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.security.jwt import TokenPayloadError, decode_token
from app.websocket.manager import connection_manager

router = APIRouter(prefix="/ws")


@router.websocket("/markets/{market_id}")
async def ws_market(websocket: WebSocket, market_id: uuid.UUID) -> None:
    await _serve(websocket, f"market:{market_id}")


@router.websocket("/events/{event_id}")
async def ws_event(websocket: WebSocket, event_id: uuid.UUID) -> None:
    await _serve(websocket, f"event:{event_id}")


@router.websocket("/user")
async def ws_user(websocket: WebSocket, token: str | None = None) -> None:
    """Auth-scoped channel for the caller's own balance/order/bet updates.

    Browsers can't set custom headers on a WebSocket handshake, so the
    access token travels as a query parameter here instead of an
    Authorization header — the one deliberate exception to that pattern in
    this API.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        user_id = decode_token(token, expected_type="access")
    except TokenPayloadError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await _serve(websocket, f"user:{user_id}")


async def _serve(websocket: WebSocket, topic: str) -> None:
    await websocket.accept()
    connection_manager.subscribe(topic, websocket)
    try:
        while True:
            # Clients don't need to send anything for updates to flow; we
            # only read to detect disconnects and answer heartbeats.
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.unsubscribe(topic, websocket)
