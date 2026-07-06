from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.middleware import REQUEST_ID_STATE_KEY


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: dict[str, Any] = field(default_factory=dict)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)


async def _app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    app_error = _coerce_app_error(exc)
    return _error_response(
        request=request,
        status_code=app_error.status_code,
        code=app_error.code,
        message=app_error.message,
        details=app_error.details,
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = _coerce_validation_error(exc)
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="request.validation_failed",
        message="Request validation failed.",
        details={"errors": validation_error.errors()},
    )


async def _http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    http_error = _coerce_http_error(exc)
    detail = http_error.detail if isinstance(http_error.detail, str) else "HTTP error."
    return _error_response(
        request=request,
        status_code=http_error.status_code,
        code="http.error",
        message=detail,
        details={},
    )


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    request_id = getattr(request.state, REQUEST_ID_STATE_KEY, None)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id} if request_id else None,
    )


def _coerce_app_error(exc: Exception) -> AppError:
    if not isinstance(exc, AppError):
        raise TypeError(f"Expected AppError, received {type(exc).__name__}")
    return exc


def _coerce_validation_error(exc: Exception) -> RequestValidationError:
    if not isinstance(exc, RequestValidationError):
        raise TypeError(f"Expected RequestValidationError, received {type(exc).__name__}")
    return exc


def _coerce_http_error(exc: Exception) -> StarletteHTTPException:
    if not isinstance(exc, StarletteHTTPException):
        raise TypeError(f"Expected StarletteHTTPException, received {type(exc).__name__}")
    return exc

