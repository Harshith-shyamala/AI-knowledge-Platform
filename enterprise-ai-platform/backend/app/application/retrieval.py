from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.application.indexing import EmbeddingGateway
from app.application.unit_of_work import UnitOfWorkFactory
from app.core.errors import AppError
from app.domain.tenancy import EmbeddedChunk

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class SearchKnowledgeCommand:
    organization_id: UUID
    workspace_id: UUID
    query: str
    top_k: int = 5


@dataclass(frozen=True)
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_index: int
    content: str
    score: float
    lexical_score: float
    vector_score: float


class Reranker(Protocol):
    def rerank(self, results: list[SearchResult]) -> list[SearchResult]:
        """Return search results in final rank order."""


@dataclass(frozen=True)
class HybridRetrievalService:
    uow_factory: UnitOfWorkFactory
    embedding_gateway: EmbeddingGateway
    reranker: Reranker

    def search(self, command: SearchKnowledgeCommand) -> list[SearchResult]:
        query = command.query.strip()
        if not query:
            raise AppError(
                code="search.empty_query",
                message="Search query must not be empty.",
                status_code=422,
                details={},
            )
        if command.top_k < 1 or command.top_k > 50:
            raise AppError(
                code="search.invalid_top_k",
                message="top_k must be between 1 and 50.",
                status_code=422,
                details={"top_k": command.top_k},
            )

        query_terms = _terms(query)
        query_vector = self.embedding_gateway.embed([query])[0]
        with self.uow_factory() as uow:
            candidates = uow.embeddings.list_for_workspace(
                command.organization_id,
                command.workspace_id,
            )

        scored = [
            self._score_candidate(candidate, query_terms, query_vector)
            for candidate in candidates
        ]
        relevant = [
            result
            for result in scored
            if result.lexical_score > 0 or result.vector_score >= _VECTOR_ONLY_THRESHOLD
        ]
        return self.reranker.rerank(relevant)[: command.top_k]

    def _score_candidate(
        self,
        candidate: EmbeddedChunk,
        query_terms: set[str],
        query_vector: list[float],
    ) -> SearchResult:
        chunk_terms = _terms(candidate.chunk.content)
        lexical_score = _lexical_score(query_terms, chunk_terms)
        vector_score = _cosine_similarity(query_vector, candidate.embedding.embedding)
        normalized_vector_score = (vector_score + 1) / 2
        hybrid_score = round((0.55 * lexical_score) + (0.45 * normalized_vector_score), 6)
        return SearchResult(
            chunk_id=candidate.chunk.id,
            document_id=candidate.chunk.document_id,
            document_version_id=candidate.chunk.document_version_id,
            chunk_index=candidate.chunk.chunk_index,
            content=candidate.chunk.content,
            score=hybrid_score,
            lexical_score=round(lexical_score, 6),
            vector_score=round(vector_score, 6),
        )


class ScoreReranker:
    def rerank(self, results: list[SearchResult]) -> list[SearchResult]:
        return sorted(
            results,
            key=lambda result: (result.score, result.lexical_score, result.vector_score),
            reverse=True,
        )


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}


def _lexical_score(query_terms: set[str], chunk_terms: set[str]) -> float:
    if not query_terms:
        return 0.0
    return len(query_terms & chunk_terms) / len(query_terms)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    dot_product = sum(left[index] * right[index] for index in range(len(left)))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)


_VECTOR_ONLY_THRESHOLD = 0.85
