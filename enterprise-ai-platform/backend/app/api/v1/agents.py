from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.agents import AgentRunResult, AgentWorkflowService, RunAgentCommand
from app.core.container import AppContainer
from app.schemas.agents import (
    AgentCitationResponse,
    AgentRunRequest,
    AgentRunResponse,
    AgentStepResponse,
)

router = APIRouter(prefix="/organizations/{organization_id}/workspaces/{workspace_id}/agents")


@router.post("/runs", response_model=AgentRunResponse, summary="Run knowledge agent")
async def run_agent(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    payload: AgentRunRequest,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> AgentRunResponse:
    auth_service.require_permission(session, organization_id, "documents.search")
    service = _agent_service(request)
    result = service.run(
        RunAgentCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_user_id=session.user.id,
            question=payload.question,
            top_k=payload.top_k,
            include_trace=payload.include_trace,
        )
    )
    return _agent_response(result)


def _agent_service(request: Request) -> AgentWorkflowService:
    container: AppContainer = request.app.state.container
    return container.agent_workflow_service


def _agent_response(result: AgentRunResult) -> AgentRunResponse:
    return AgentRunResponse(
        answer=result.answer,
        citations=[
            AgentCitationResponse(
                document_id=citation.document_id,
                document_version_id=citation.document_version_id,
                chunk_id=citation.chunk_id,
                quote=citation.quote,
                score=citation.score,
            )
            for citation in result.citations
        ],
        steps=[
            AgentStepResponse(
                name=step.name,
                status=step.status,
                summary=step.summary,
                metadata=step.metadata,
            )
            for step in result.steps
        ],
        prompt_version=result.prompt_version,
        workflow_version=result.workflow_version,
    )
