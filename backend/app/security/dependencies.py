from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.jwt import TokenPayloadError, decode_token


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        user_id = decode_token(token, expected_type="access")
    except TokenPayloadError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user


def require_role(role_code: str):
    """Dependency factory: Depends(require_role("admin")) rejects with 403
    unless the authenticated user carries that role."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if role_code not in {role.code for role in user.roles}:
            raise ForbiddenError(f"Requires role: {role_code}")
        return user

    return _check
