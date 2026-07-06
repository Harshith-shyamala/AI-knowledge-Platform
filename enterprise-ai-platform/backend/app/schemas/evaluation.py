from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationExampleRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    expected_answer: str = Field(min_length=1, max_length=4000)


class EvaluationRunRequest(BaseModel):
    examples: list[EvaluationExampleRequest] = Field(min_length=1, max_length=25)
    top_k: int = Field(default=5, ge=1, le=10)


class EvaluationScoreResponse(BaseModel):
    name: str
    score: float
    passed: bool
    threshold: float
    explanation: str
    evaluator_version: str


class EvaluationExampleResultResponse(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    citation_count: int
    scores: list[EvaluationScoreResponse]


class EvaluationRunResponse(BaseModel):
    run_id: UUID
    examples: list[EvaluationExampleResultResponse]
    aggregate_scores: list[EvaluationScoreResponse]
    prompt_version: str
    workflow_version: str


class EvaluationMetricsResponse(BaseModel):
    evaluators: list[EvaluationScoreResponse]
