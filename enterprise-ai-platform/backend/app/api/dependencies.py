from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.auth import AuthenticatedSession, AuthService
from app.core.container import AppContainer
from app.core.errors import AppError

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
    container: AppContainer = request.app.state.container
    return container.auth_service


def get_current_session(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],  # noqa: UP045
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedSession:
    if credentials is None:
        raise AppError(
            code="auth.missing_token",
            message="Bearer token is required.",
            status_code=401,
            details={},
        )
    return auth_service.authenticate_access_token(credentials.credentials)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentSessionDep = Annotated[AuthenticatedSession, Depends(get_current_session)]
