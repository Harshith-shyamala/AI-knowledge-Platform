from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.factory import create_app

app = create_app()


def run() -> None:
    """Run the API with Uvicorn for local development."""

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_config=None,
    )
