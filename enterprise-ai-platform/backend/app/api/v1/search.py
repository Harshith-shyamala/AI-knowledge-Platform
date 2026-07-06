from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.retrieval import HybridRetrievalService, SearchKnowledgeCommand
from app.core.container import AppContainer
from app.schemas.search import SearchRequest, SearchResponse, SearchResultResponse

router = APIRouter(prefix="/organizations/{organization_id}/workspaces/{workspace_id}/search")


@router.post("", response_model=SearchResponse, summary="Search workspace knowledge")
async def search_workspace(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    payload: SearchRequest,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> SearchResponse:
    auth_service.require_permission(session, organization_id, "documents.search")
    service = _retrieval_service(request)
    results = service.search(
        SearchKnowledgeCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            query=payload.query,
            top_k=payload.top_k,
        )
    )
    return SearchResponse(
        query=payload.query,
        results=[
            SearchResultResponse(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_version_id=result.document_version_id,
                chunk_index=result.chunk_index,
                content=result.content,
                score=result.score,
                lexical_score=result.lexical_score,
                vector_score=result.vector_score,
            )
            for result in results
        ],
    )


def _retrieval_service(request: Request) -> HybridRetrievalService:
    container: AppContainer = request.app.state.container
    return container.retrieval_service
