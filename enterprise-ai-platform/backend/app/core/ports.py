from __future__ import annotations

from typing import Protocol

from app.schemas.health import ReadinessDependency


class ReadinessProbe(Protocol):
    async def check(self) -> ReadinessDependency:
        """Return readiness details for one dependency."""

