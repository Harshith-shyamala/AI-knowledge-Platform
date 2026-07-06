from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.tenancy import (
    ChunkEmbedding,
    Citation,
    Conversation,
    Document,
    DocumentVersion,
    EmbeddedChunk,
    KnowledgeChunk,
    Message,
    Organization,
    OrganizationMembership,
    User,
    Workspace,
)


class OrganizationRepository(Protocol):
    def add(self, organization: Organization) -> None:
        """Persist an organization."""

    def get(self, organization_id: UUID) -> Organization | None:
        """Return an organization by id."""

    def get_by_slug(self, slug: str) -> Organization | None:
        """Return an organization by slug."""

    def list(self) -> list[Organization]:
        """Return all organizations visible to the current service boundary."""


class WorkspaceRepository(Protocol):
    def add(self, workspace: Workspace) -> None:
        """Persist a workspace."""

    def get(self, organization_id: UUID, workspace_id: UUID) -> Workspace | None:
        """Return a workspace scoped to an organization."""

    def get_by_slug(self, organization_id: UUID, slug: str) -> Workspace | None:
        """Return a workspace by tenant-scoped slug."""

    def list_for_organization(self, organization_id: UUID) -> list[Workspace]:
        """Return workspaces scoped to one organization."""


class UserRepository(Protocol):
    def add(self, user: User) -> None:
        """Persist a user."""

    def get(self, user_id: UUID) -> User | None:
        """Return a user by id."""

    def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email."""


class OrganizationMembershipRepository(Protocol):
    def add(self, membership: OrganizationMembership) -> None:
        """Persist an organization membership."""

    def get(self, organization_id: UUID, user_id: UUID) -> OrganizationMembership | None:
        """Return a membership for one user and organization."""

    def list_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
        """Return memberships for a user."""


class DocumentRepository(Protocol):
    def add(self, document: Document) -> None:
        """Persist a document."""

    def update(self, document: Document) -> None:
        """Update a document."""

    def get(self, organization_id: UUID, workspace_id: UUID, document_id: UUID) -> Document | None:
        """Return a tenant-scoped document."""

    def list_for_workspace(self, organization_id: UUID, workspace_id: UUID) -> list[Document]:
        """Return documents for a workspace."""


class DocumentVersionRepository(Protocol):
    def add(self, version: DocumentVersion) -> None:
        """Persist a document version."""

    def latest_version_number(self, document_id: UUID) -> int:
        """Return latest version number for a document."""

    def list_for_document(self, document_id: UUID) -> list[DocumentVersion]:
        """Return versions for a document."""

    def get(self, version_id: UUID) -> DocumentVersion | None:
        """Return a document version by id."""


class KnowledgeChunkRepository(Protocol):
    def add_many(self, chunks: list[KnowledgeChunk]) -> None:
        """Persist chunks."""

    def delete_for_document_version(self, document_version_id: UUID) -> None:
        """Delete chunks for a specific document version."""

    def list_for_document(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        document_id: UUID,
    ) -> list[KnowledgeChunk]:
        """Return chunks for a tenant-scoped document."""


class ChunkEmbeddingRepository(Protocol):
    def add_many(self, embeddings: list[ChunkEmbedding]) -> None:
        """Persist chunk embeddings."""

    def delete_for_document_version(self, document_version_id: UUID) -> None:
        """Delete embeddings for chunks from a specific document version."""

    def list_for_workspace(self, organization_id: UUID, workspace_id: UUID) -> list[EmbeddedChunk]:
        """Return embedded chunks scoped to a workspace."""


class ConversationRepository(Protocol):
    def add(self, conversation: Conversation) -> None:
        """Persist a conversation."""

    def get(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation | None:
        """Return a tenant-scoped conversation for one user."""

    def list_for_user(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        user_id: UUID,
    ) -> list[Conversation]:
        """Return conversations for one user in one workspace."""


class MessageRepository(Protocol):
    def add(self, message: Message) -> None:
        """Persist a chat message."""

    def list_for_conversation(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]:
        """Return messages for a tenant-scoped conversation."""


class CitationRepository(Protocol):
    def add_many(self, citations: list[Citation]) -> None:
        """Persist citations."""

    def list_for_message(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        message_id: UUID,
    ) -> list[Citation]:
        """Return citations for a tenant-scoped message."""
