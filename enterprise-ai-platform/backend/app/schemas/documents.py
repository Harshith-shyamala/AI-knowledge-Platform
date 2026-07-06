from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    owner_user_id: UUID
    title: str
    source_type: str
    mime_type: str
    status: str
    current_version_id: Optional[UUID]  # noqa: UP045
    created_at: datetime
    updated_at: datetime


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    document_id: UUID
    version_number: int
    storage_key: str
    original_filename: str
    file_sha256: str
    size_bytes: int
    created_by_user_id: UUID
    created_at: datetime


class UploadDocumentResponse(BaseModel):
    document: DocumentResponse
    version: DocumentVersionResponse
    job_id: UUID
    duplicate_hint: bool


class IndexDocumentResponse(BaseModel):
    document: DocumentResponse
    chunks_indexed: int
    embeddings_indexed: int
    embedding_provider: str
    embedding_model: str


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_index: int
    content: str
    content_sha256: str
    token_count: int
    created_at: datetime
