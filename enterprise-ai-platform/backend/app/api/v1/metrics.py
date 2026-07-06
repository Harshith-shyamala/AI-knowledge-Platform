from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.core.metrics import MetricsRegistry

router = APIRouter(prefix="/metrics")


@router.get(
    "",
    response_class=PlainTextResponse,
    summary="Prometheus metrics",
)
async def metrics(request: Request) -> PlainTextResponse:
    registry: MetricsRegistry = request.app.state.metrics_registry
    return PlainTextResponse(
        content=registry.render_prometheus(),
        media_type="text/plain; version=0.0.4",
    )
