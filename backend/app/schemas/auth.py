from __future__ import annotations

import typing
import uuid

from pydantic import BaseModel, EmailStr, Field

if typing.TYPE_CHECKING:
    from app.models.user import User


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    status: str
    roles: list[str]

    @classmethod
    def from_user(cls, user: User) -> UserRead:
        status_value = user.status.value if hasattr(user.status, "value") else user.status
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=status_value,
            roles=[role.code for role in user.roles],
        )
