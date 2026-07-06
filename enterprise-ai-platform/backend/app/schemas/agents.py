from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)
    include_trace: bool = True


class AgentStepResponse(BaseModel):
    name: str
    status: str
    summary: str
    metadata: dict[str, str]


class AgentCitationResponse(BaseModel):
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    quote: str
    score: float


class AgentRunResponse(BaseModel):
    answer: str
    citations: list[AgentCitationResponse]
    steps: list[AgentStepResponse]
    prompt_version: str
    workflow_version: str
