from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

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
from app.application.unit_of_work import UnitOfWork
from app.infrastructure.persistence.repositories import (
    SQLAlchemyChunkEmbeddingRepository,
    SQLAlchemyCitationRepository,
    SQLAlchemyConversationRepository,
    SQLAlchemyDocumentRepository,
    SQLAlchemyDocumentVersionRepository,
    SQLAlchemyKnowledgeChunkRepository,
    SQLAlchemyMessageRepository,
    SQLAlchemyOrganizationMembershipRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyUserRepository,
    SQLAlchemyWorkspaceRepository,
)


class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.organizations: OrganizationRepository
        self.workspaces: WorkspaceRepository
        self.users: UserRepository
        self.organization_memberships: OrganizationMembershipRepository
        self.documents: DocumentRepository
        self.document_versions: DocumentVersionRepository
        self.chunks: KnowledgeChunkRepository
        self.embeddings: ChunkEmbeddingRepository
        self.conversations: ConversationRepository
        self.messages: MessageRepository
        self.citations: CitationRepository

    def __enter__(self) -> UnitOfWork:
        self._session = self._session_factory()
        self.organizations = SQLAlchemyOrganizationRepository(self._session)
        self.workspaces = SQLAlchemyWorkspaceRepository(self._session)
        self.users = SQLAlchemyUserRepository(self._session)
        self.organization_memberships = SQLAlchemyOrganizationMembershipRepository(self._session)
        self.documents = SQLAlchemyDocumentRepository(self._session)
        self.document_versions = SQLAlchemyDocumentVersionRepository(self._session)
        self.chunks = SQLAlchemyKnowledgeChunkRepository(self._session)
        self.embeddings = SQLAlchemyChunkEmbeddingRepository(self._session)
        self.conversations = SQLAlchemyConversationRepository(self._session)
        self.messages = SQLAlchemyMessageRepository(self._session)
        self.citations = SQLAlchemyCitationRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        if exc_type is not None:
            self.rollback()

        self._session.close()

    def commit(self) -> None:
        self._require_session().commit()

    def rollback(self) -> None:
        self._require_session().rollback()

    def _require_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of work has not been entered.")
        return self._session
