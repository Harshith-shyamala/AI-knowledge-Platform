from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    display_name: str = Field(min_length=1, max_length=255)
    organization_name: str = Field(min_length=1, max_length=255)
    organization_slug: Optional[str] = Field(default=None, min_length=1, max_length=120)  # noqa: UP045


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    created_at: datetime
    permissions: list[str]


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    is_active: bool
    created_at: datetime


class AuthSessionResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
    memberships: list[MembershipResponse]


class CurrentUserResponse(BaseModel):
    user: UserResponse
    memberships: list[MembershipResponse]

