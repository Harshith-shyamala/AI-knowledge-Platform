from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol

from app.application.repositories import (
    ChunkEmbeddingRepository,
    CitationRepository,
    ConversationRepository,
    DocumentRepository,
    DocumentVersionRepository,
    KnowledgeChunkRepository,
    MessageRepository,
    OrganizationMembershipRepository,
    OrganizationRepository,
    UserRepository,
    WorkspaceRepository,
)


class UnitOfWork(Protocol):
    organizations: OrganizationRepository
    workspaces: WorkspaceRepository
    users: UserRepository
    organization_memberships: OrganizationMembershipRepository
    documents: DocumentRepository
    document_versions: DocumentVersionRepository
    chunks: KnowledgeChunkRepository
    embeddings: ChunkEmbeddingRepository
    conversations: ConversationRepository
    messages: MessageRepository
    citations: CitationRepository

    def __enter__(self) -> UnitOfWork:
        """Open a transaction boundary."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit or roll back transaction boundary."""

    def commit(self) -> None:
        """Commit pending changes."""

    def rollback(self) -> None:
        """Roll back pending changes."""


UnitOfWorkFactory = Callable[[], UnitOfWork]
