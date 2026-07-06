from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from app.core.config import Settings
from app.core.ports import ReadinessProbe
from app.schemas.health import HealthResponse, ReadinessDependency, ReadinessResponse


@dataclass(frozen=True)
class HealthService:
    """Application-level health service.

    The API route delegates here so future database, Redis, queue, and model-provider
    checks can be added without putting operational behavior inside FastAPI handlers.
    """

    settings: Settings
    readiness_probes: Sequence[ReadinessProbe]

    def liveness(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=self.settings.service_name,
            environment=self.settings.environment,
            version=self.settings.api_version,
        )

    async def readiness(self) -> ReadinessResponse:
        started_at = perf_counter()

        if not self.settings.readiness_dependencies_enabled:
            return ReadinessResponse(
                status="ready",
                service=self.settings.service_name,
                dependencies=[],
                latency_ms=self._elapsed_ms(started_at),
            )

        dependencies = [await probe.check() for probe in self.readiness_probes]
        status: Literal["ready", "degraded"] = (
            "ready" if all(item.status == "ready" for item in dependencies) else "degraded"
        )

        return ReadinessResponse(
            status=status,
            service=self.settings.service_name,
            dependencies=dependencies,
            latency_ms=self._elapsed_ms(started_at),
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((perf_counter() - started_at) * 1000, 3)


@dataclass(frozen=True)
class StaticReadinessProbe:
    """Readiness probe used until external infrastructure is introduced."""

    name: str
    ready: bool = True

    async def check(self) -> ReadinessDependency:
        return ReadinessDependency(
            name=self.name,
            status="ready" if self.ready else "degraded",
            latency_ms=0.0,
        )
