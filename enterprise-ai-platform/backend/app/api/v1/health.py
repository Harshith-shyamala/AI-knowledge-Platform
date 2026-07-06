from fastapi import APIRouter, Request, status

from app.application.health import HealthService
from app.core.container import AppContainer
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health")


def _health_service(request: Request) -> HealthService:
    container: AppContainer = request.app.state.container
    return container.health_service


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
)
async def live(request: Request) -> HealthResponse:
    return _health_service(request).liveness()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
)
async def ready(request: Request) -> ReadinessResponse:
    return await _health_service(request).readiness()

