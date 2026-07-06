from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.evaluation import (
    EvaluationExample,
    EvaluationRunResult,
    EvaluationScore,
    EvaluationService,
    RunEvaluationCommand,
)
from app.core.container import AppContainer
from app.schemas.evaluation import (
    EvaluationExampleResultResponse,
    EvaluationMetricsResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationScoreResponse,
)

router = APIRouter(prefix="/organizations/{organization_id}/workspaces/{workspace_id}/evaluation")


@router.get("", response_model=EvaluationMetricsResponse, summary="Get evaluation metrics")
async def get_evaluation_metrics(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> EvaluationMetricsResponse:
    del workspace_id
    auth_service.require_permission(session, organization_id, "metrics.view")
    service = _evaluation_service(request)
    return EvaluationMetricsResponse(
        evaluators=[_score_response(score) for score in service.evaluator_catalog()]
    )


@router.post("/runs", response_model=EvaluationRunResponse, summary="Run evaluation")
async def run_evaluation(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    payload: EvaluationRunRequest,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> EvaluationRunResponse:
    auth_service.require_permission(session, organization_id, "metrics.view")
    service = _evaluation_service(request)
    result = service.run(
        RunEvaluationCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_user_id=session.user.id,
            examples=[
                EvaluationExample(
                    question=example.question,
                    expected_answer=example.expected_answer,
                )
                for example in payload.examples
            ],
            top_k=payload.top_k,
        )
    )
    return _run_response(result)


def _evaluation_service(request: Request) -> EvaluationService:
    container: AppContainer = request.app.state.container
    return container.evaluation_service


def _run_response(result: EvaluationRunResult) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        run_id=result.run_id,
        examples=[
            EvaluationExampleResultResponse(
                question=example.question,
                expected_answer=example.expected_answer,
                actual_answer=example.actual_answer,
                citation_count=example.citation_count,
                scores=[_score_response(score) for score in example.scores],
            )
            for example in result.examples
        ],
        aggregate_scores=[_score_response(score) for score in result.aggregate_scores],
        prompt_version=result.prompt_version,
        workflow_version=result.workflow_version,
    )


def _score_response(score: EvaluationScore) -> EvaluationScoreResponse:
    return EvaluationScoreResponse(
        name=score.name,
        score=score.score,
        passed=score.passed,
        threshold=score.threshold,
        explanation=score.explanation,
        evaluator_version=score.evaluator_version,
    )
