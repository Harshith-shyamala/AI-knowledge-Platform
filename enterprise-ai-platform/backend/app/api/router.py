from fastapi import APIRouter

from app.api.v1 import (
    agents,
    auth,
    chat,
    documents,
    evaluation,
    health,
    metrics,
    organizations,
    search,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(evaluation.router, tags=["evaluation"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(organizations.router, tags=["organizations"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(chat.router, tags=["chat"])
