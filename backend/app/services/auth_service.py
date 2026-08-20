from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, UnauthorizedError
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse, UserRead
from app.security.jwt import (
    TokenPayloadError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.security.password import hash_password, verify_password
from app.services.wallet_service import WalletService

DEFAULT_ROLE_CODE = "user"


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)

    async def register(self, payload: RegisterRequest) -> UserRead:
        email = payload.email.lower()
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise ConflictError(
                "An account with this email already exists.", code="EMAIL_ALREADY_REGISTERED"
            )

        default_role = await self.roles.get_by_code(DEFAULT_ROLE_CODE)
        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )
        if default_role is not None:
            user.roles.append(default_role)

        await self.users.add(user)
        await WalletService(self.session).create_wallet(user.id)
        await self.session.commit()
        await self.session.refresh(user, attribute_names=["roles"])
        return UserRead.from_user(user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.", code="INVALID_CREDENTIALS")
        if not user.is_active:
            raise UnauthorizedError("This account is not active.", code="ACCOUNT_INACTIVE")
        return user

    async def issue_tokens(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            user_id = decode_token(refresh_token, expected_type="refresh")
        except TokenPayloadError as exc:
            raise UnauthorizedError(str(exc), code="INVALID_REFRESH_TOKEN") from exc

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists.", code="INVALID_REFRESH_TOKEN")
        return await self.issue_tokens(user)
