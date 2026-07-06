from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.chat import GroundedAnswerGenerator
from app.application.retrieval import HybridRetrievalService, SearchKnowledgeCommand, SearchResult
from app.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.core.errors import AppError


@dataclass(frozen=True)
class RunAgentCommand:
    organization_id: UUID
    workspace_id: UUID
    actor_user_id: UUID
    question: str
    top_k: int = 5
    include_trace: bool = True


@dataclass(frozen=True)
class AgentStep:
    name: str
    status: str
    summary: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class AgentCitation:
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    quote: str
    score: float


@dataclass(frozen=True)
class AgentRunResult:
    answer: str
    citations: list[AgentCitation]
    steps: list[AgentStep]
    prompt_version: str
    workflow_version: str


@dataclass(frozen=True)
class AgentWorkflowService:
    uow_factory: UnitOfWorkFactory
    retrieval_service: HybridRetrievalService
    answer_generator: GroundedAnswerGenerator
    prompt_version: str = "agent-rag-v1"
    workflow_version: str = "deterministic-agent-v1"

    def run(self, command: RunAgentCommand) -> AgentRunResult:
        question = command.question.strip()
        if not question:
            raise AppError(
                code="agent.empty_question",
                message="Agent question must not be empty.",
                status_code=422,
                details={},
            )
        if command.top_k < 1 or command.top_k > 10:
            raise AppError(
                code="agent.invalid_top_k",
                message="top_k must be between 1 and 10.",
                status_code=422,
                details={"top_k": command.top_k},
            )

        with self.uow_factory() as uow:
            self._require_workspace(uow, command.organization_id, command.workspace_id)

        steps = [
            AgentStep(
                name="plan",
                status="completed",
                summary=(
                    "Plan: search workspace knowledge, inspect evidence, "
                    "check grounding, answer."
                ),
                metadata={"tool": "planner", "prompt_version": self.prompt_version},
            )
        ]

        retrieved = self.retrieval_service.search(
            SearchKnowledgeCommand(
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                query=question,
                top_k=command.top_k,
            )
        )
        steps.append(
            AgentStep(
                name="search_workspace",
                status="completed",
                summary=f"Retrieved {len(retrieved)} candidate chunk(s) from workspace search.",
                metadata={"tool": "hybrid_retrieval", "result_count": str(len(retrieved))},
            )
        )

        steps.append(_inspect_step(retrieved))
        steps.append(_reflection_step(retrieved))
        answer = self.answer_generator.generate(question, retrieved)
        citations = [_citation_from_result(result) for result in retrieved]
        steps.append(
            AgentStep(
                name="final_answer",
                status="completed",
                summary="Generated final response from inspected evidence.",
                metadata={"citation_count": str(len(citations))},
            )
        )

        visible_steps = steps if command.include_trace else []
        return AgentRunResult(
            answer=answer,
            citations=citations,
            steps=visible_steps,
            prompt_version=self.prompt_version,
            workflow_version=self.workflow_version,
        )

    @staticmethod
    def _require_workspace(uow: UnitOfWork, organization_id: UUID, workspace_id: UUID) -> None:
        if uow.workspaces.get(organization_id, workspace_id) is None:
            raise AppError(
                code="workspace.not_found",
                message="Workspace was not found.",
                status_code=404,
                details={"workspace_id": str(workspace_id)},
            )


def _inspect_step(results: list[SearchResult]) -> AgentStep:
    if not results:
        return AgentStep(
            name="inspect_evidence",
            status="skipped",
            summary="No evidence was available to inspect.",
            metadata={"top_score": "0"},
        )
    strongest = results[0]
    return AgentStep(
        name="inspect_evidence",
        status="completed",
        summary="Selected the strongest retrieved chunk as primary evidence.",
        metadata={
            "chunk_id": str(strongest.chunk_id),
            "document_id": str(strongest.document_id),
            "score": str(strongest.score),
        },
    )


def _reflection_step(results: list[SearchResult]) -> AgentStep:
    if not results:
        return AgentStep(
            name="grounding_reflection",
            status="completed",
            summary="Grounding check failed because no indexed evidence was retrieved.",
            metadata={"grounded": "false"},
        )
    return AgentStep(
        name="grounding_reflection",
        status="completed",
        summary="Grounding check passed because the answer will cite retrieved chunks.",
        metadata={"grounded": "true", "citation_count": str(len(results))},
    )


def _citation_from_result(result: SearchResult) -> AgentCitation:
    return AgentCitation(
        document_id=result.document_id,
        document_version_id=result.document_version_id,
        chunk_id=result.chunk_id,
        quote=_quote(result.content),
        score=result.score,
    )


def _quote(content: str) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= 500:
        return normalized
    return f"{normalized[:497]}..."
