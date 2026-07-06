from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.config import Environment


class HealthResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: Literal["ok"]
    service: str
    environment: Environment
    version: str


class ReadinessDependency(BaseModel):
    name: str
    status: Literal["ready", "degraded"]
    latency_ms: float


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    service: str
    dependencies: list[ReadinessDependency]
    latency_ms: float

