from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.metrics import MetricsRegistry

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_KEY = "request_id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid4()))
        setattr(request.state, REQUEST_ID_STATE_KEY, request_id)

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, metrics_registry: MetricsRegistry) -> None:
        super().__init__(app)
        self._metrics_registry = metrics_registry

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            self._record(request, 500, started_at)
            raise

        self._record(request, response.status_code, started_at)
        return response

    def _record(self, request: Request, status_code: int, started_at: float) -> None:
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        latency_ms = round((perf_counter() - started_at) * 1000, 6)
        self._metrics_registry.record_request(
            method=request.method,
            path=path,
            status_code=status_code,
            latency_ms=latency_ms,
        )
