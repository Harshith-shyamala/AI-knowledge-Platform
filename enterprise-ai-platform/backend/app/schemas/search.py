from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchResultResponse(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_index: int
    content: str
    score: float
    lexical_score: float
    vector_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultResponse]

