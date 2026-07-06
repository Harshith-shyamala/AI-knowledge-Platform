from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.container import AppContainer
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.metrics import MetricsRegistry
from app.core.middleware import MetricsMiddleware, RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)

    app = FastAPI(
        title="Enterprise AI Knowledge Platform API",
        version="0.1.0",
        description="Production-grade backend API for enterprise knowledge intelligence.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.state.settings = resolved_settings
    app.state.container = AppContainer.build(resolved_settings)
    app.state.metrics_registry = MetricsRegistry()

    app.add_middleware(MetricsMiddleware, metrics_registry=app.state.metrics_registry)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in resolved_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app
