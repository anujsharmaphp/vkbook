import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt

from app.core.config import get_settings

settings = get_settings()

TokenType = Literal["access", "refresh"]


class TokenPayloadError(Exception):
    """Raised for any invalid, expired, or wrong-type token."""


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(str(user_id), "access", expires_delta)


def create_refresh_token(user_id: uuid.UUID) -> str:
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    return _create_token(str(user_id), "refresh", expires_delta)


def decode_token(token: str, expected_type: TokenType) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenPayloadError("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise TokenPayloadError(f"Expected a {expected_type} token")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenPayloadError("Malformed token subject") from exc
