from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Organization:
    id: UUID
    name: str
    slug: str
    plan: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Workspace:
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    display_name: str
    password_hash: str
    is_active: bool
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class OrganizationMembership:
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    created_at: datetime


@dataclass(frozen=True)
class Document:
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    owner_user_id: UUID
    title: str
    source_type: str
    mime_type: str
    status: str
    current_version_id: UUID | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DocumentVersion:
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


@dataclass(frozen=True)
class KnowledgeChunk:
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


@dataclass(frozen=True)
class ChunkEmbedding:
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    chunk_id: UUID
    provider: str
    model: str
    dimensions: int
    embedding: list[float]
    created_at: datetime


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: KnowledgeChunk
    embedding: ChunkEmbedding


@dataclass(frozen=True)
class Conversation:
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    user_id: UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass(frozen=True)
class Message:
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


@dataclass(frozen=True)
class Citation:
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    message_id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    quote: str
    score: float
    created_at: datetime
