from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.auth import AuthenticatedSession, AuthService, LoginCommand, RegisterCommand
from app.application.security import TokenPair
from app.schemas.auth import (
    AuthSessionResponse,
    CurrentUserResponse,
    LoginRequest,
    MembershipResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user and bootstrap organization",
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthServiceDep,
) -> AuthSessionResponse:
    session = auth_service.register(
        RegisterCommand(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            organization_name=payload.organization_name,
            organization_slug=payload.organization_slug,
        )
    )
    return _session_response(session, auth_service)


@router.post("/login", response_model=AuthSessionResponse, summary="Login")
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> AuthSessionResponse:
    session = auth_service.login(LoginCommand(email=payload.email, password=payload.password))
    return _session_response(session, auth_service)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh tokens")
async def refresh(
    payload: RefreshRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    return _token_response(auth_service.refresh(payload.refresh_token))


@router.get("/me", response_model=CurrentUserResponse, summary="Current user")
async def me(
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> CurrentUserResponse:
    return CurrentUserResponse(
        user=_user_response(session),
        memberships=_membership_responses(session, auth_service),
    )


def _session_response(
    session: AuthenticatedSession,
    auth_service: AuthService,
) -> AuthSessionResponse:
    return AuthSessionResponse(
        user=_user_response(session),
        tokens=_token_response(session.tokens),
        memberships=_membership_responses(session, auth_service),
    )


def _user_response(session: AuthenticatedSession) -> UserResponse:
    return UserResponse(
        id=session.user.id,
        email=session.user.email,
        display_name=session.user.display_name,
        is_active=session.user.is_active,
        created_at=session.user.created_at,
    )


def _token_response(tokens: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


def _membership_responses(
    session: AuthenticatedSession,
    auth_service: AuthService,
) -> list[MembershipResponse]:
    return [
        MembershipResponse(
            id=membership.id,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            role=membership.role,
            created_at=membership.created_at,
            permissions=sorted(auth_service.rbac_policy.permissions_for_role(membership.role)),
        )
        for membership in session.memberships
    ]
