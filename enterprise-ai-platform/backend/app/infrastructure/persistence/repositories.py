from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

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
from app.infrastructure.persistence.models import (
    ChunkEmbeddingModel,
    CitationModel,
    ConversationModel,
    DocumentModel,
    DocumentVersionModel,
    KnowledgeChunkModel,
    MessageModel,
    OrganizationMembershipModel,
    OrganizationModel,
    UserModel,
    WorkspaceModel,
)


class SQLAlchemyOrganizationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, organization: Organization) -> None:
        self._session.add(_organization_to_model(organization))

    def get(self, organization_id: UUID) -> Organization | None:
        model = self._session.get(OrganizationModel, organization_id)
        return _organization_from_model(model) if model is not None else None

    def get_by_slug(self, slug: str) -> Organization | None:
        model = self._session.scalar(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        return _organization_from_model(model) if model is not None else None

    def list(self) -> list[Organization]:
        models = self._session.scalars(
            select(OrganizationModel).order_by(OrganizationModel.created_at)
        ).all()
        return [_organization_from_model(model) for model in models]


class SQLAlchemyWorkspaceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, workspace: Workspace) -> None:
        self._session.add(_workspace_to_model(workspace))

    def get(self, organization_id: UUID, workspace_id: UUID) -> Workspace | None:
        model = self._session.scalar(
            select(WorkspaceModel).where(
                WorkspaceModel.organization_id == organization_id,
                WorkspaceModel.id == workspace_id,
            )
        )
        return _workspace_from_model(model) if model is not None else None

    def get_by_slug(self, organization_id: UUID, slug: str) -> Workspace | None:
        model = self._session.scalar(
            select(WorkspaceModel).where(
                WorkspaceModel.organization_id == organization_id,
                WorkspaceModel.slug == slug,
            )
        )
        return _workspace_from_model(model) if model is not None else None

    def list_for_organization(self, organization_id: UUID) -> list[Workspace]:
        models = self._session.scalars(
            select(WorkspaceModel)
            .where(WorkspaceModel.organization_id == organization_id)
            .order_by(WorkspaceModel.created_at)
        ).all()
        return [_workspace_from_model(model) for model in models]


class SQLAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(_user_to_model(user))

    def get(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _user_from_model(model) if model is not None else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return _user_from_model(model) if model is not None else None


class SQLAlchemyOrganizationMembershipRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, membership: OrganizationMembership) -> None:
        self._session.add(_membership_to_model(membership))

    def get(self, organization_id: UUID, user_id: UUID) -> OrganizationMembership | None:
        model = self._session.scalar(
            select(OrganizationMembershipModel).where(
                OrganizationMembershipModel.organization_id == organization_id,
                OrganizationMembershipModel.user_id == user_id,
            )
        )
        return _membership_from_model(model) if model is not None else None

    def list_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
        models = self._session.scalars(
            select(OrganizationMembershipModel)
            .where(OrganizationMembershipModel.user_id == user_id)
            .order_by(OrganizationMembershipModel.created_at)
        ).all()
        return [_membership_from_model(model) for model in models]


class SQLAlchemyDocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: Document) -> None:
        self._session.add(_document_to_model(document))

    def update(self, document: Document) -> None:
        model = self._session.get(DocumentModel, document.id)
        if model is None:
            return
        model.title = document.title
        model.mime_type = document.mime_type
        model.status = document.status
        model.current_version_id = document.current_version_id
        model.updated_at = document.updated_at

    def get(self, organization_id: UUID, workspace_id: UUID, document_id: UUID) -> Document | None:
        model = self._session.scalar(
            select(DocumentModel).where(
                DocumentModel.organization_id == organization_id,
                DocumentModel.workspace_id == workspace_id,
                DocumentModel.id == document_id,
                DocumentModel.deleted_at.is_(None),
            )
        )
        return _document_from_model(model) if model is not None else None

    def list_for_workspace(self, organization_id: UUID, workspace_id: UUID) -> list[Document]:
        models = self._session.scalars(
            select(DocumentModel)
            .where(
                DocumentModel.organization_id == organization_id,
                DocumentModel.workspace_id == workspace_id,
                DocumentModel.deleted_at.is_(None),
            )
            .order_by(DocumentModel.created_at)
        ).all()
        return [_document_from_model(model) for model in models]


class SQLAlchemyDocumentVersionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, version: DocumentVersion) -> None:
        self._session.add(_document_version_to_model(version))

    def latest_version_number(self, document_id: UUID) -> int:
        latest = self._session.scalar(
            select(func.max(DocumentVersionModel.version_number)).where(
                DocumentVersionModel.document_id == document_id
            )
        )
        return int(latest or 0)

    def list_for_document(self, document_id: UUID) -> list[DocumentVersion]:
        models = self._session.scalars(
            select(DocumentVersionModel)
            .where(DocumentVersionModel.document_id == document_id)
            .order_by(DocumentVersionModel.version_number)
        ).all()
        return [_document_version_from_model(model) for model in models]

    def get(self, version_id: UUID) -> DocumentVersion | None:
        model = self._session.get(DocumentVersionModel, version_id)
        return _document_version_from_model(model) if model is not None else None


class SQLAlchemyKnowledgeChunkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, chunks: list[KnowledgeChunk]) -> None:
        self._session.add_all([_chunk_to_model(chunk) for chunk in chunks])

    def delete_for_document_version(self, document_version_id: UUID) -> None:
        self._session.execute(
            delete(KnowledgeChunkModel).where(
                KnowledgeChunkModel.document_version_id == document_version_id
            )
        )

    def list_for_document(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        document_id: UUID,
    ) -> list[KnowledgeChunk]:
        models = self._session.scalars(
            select(KnowledgeChunkModel)
            .where(
                KnowledgeChunkModel.organization_id == organization_id,
                KnowledgeChunkModel.workspace_id == workspace_id,
                KnowledgeChunkModel.document_id == document_id,
            )
            .order_by(KnowledgeChunkModel.chunk_index)
        ).all()
        return [_chunk_from_model(model) for model in models]


class SQLAlchemyChunkEmbeddingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, embeddings: list[ChunkEmbedding]) -> None:
        self._session.add_all([_embedding_to_model(embedding) for embedding in embeddings])

    def delete_for_document_version(self, document_version_id: UUID) -> None:
        chunk_ids = select(KnowledgeChunkModel.id).where(
            KnowledgeChunkModel.document_version_id == document_version_id
        )
        self._session.execute(
            delete(ChunkEmbeddingModel).where(ChunkEmbeddingModel.chunk_id.in_(chunk_ids))
        )

    def list_for_workspace(self, organization_id: UUID, workspace_id: UUID) -> list[EmbeddedChunk]:
        rows = self._session.execute(
            select(KnowledgeChunkModel, ChunkEmbeddingModel)
            .join(ChunkEmbeddingModel, ChunkEmbeddingModel.chunk_id == KnowledgeChunkModel.id)
            .where(
                KnowledgeChunkModel.organization_id == organization_id,
                KnowledgeChunkModel.workspace_id == workspace_id,
                ChunkEmbeddingModel.organization_id == organization_id,
                ChunkEmbeddingModel.workspace_id == workspace_id,
            )
            .order_by(KnowledgeChunkModel.created_at, KnowledgeChunkModel.chunk_index)
        ).all()
        return [
            EmbeddedChunk(
                chunk=_chunk_from_model(chunk_model),
                embedding=_embedding_from_model(embedding_model),
            )
            for chunk_model, embedding_model in rows
        ]


class SQLAlchemyConversationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, conversation: Conversation) -> None:
        self._session.add(_conversation_to_model(conversation))

    def get(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation | None:
        model = self._session.scalar(
            select(ConversationModel).where(
                ConversationModel.organization_id == organization_id,
                ConversationModel.workspace_id == workspace_id,
                ConversationModel.id == conversation_id,
                ConversationModel.user_id == user_id,
                ConversationModel.deleted_at.is_(None),
            )
        )
        return _conversation_from_model(model) if model is not None else None

    def list_for_user(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        user_id: UUID,
    ) -> list[Conversation]:
        models = self._session.scalars(
            select(ConversationModel)
            .where(
                ConversationModel.organization_id == organization_id,
                ConversationModel.workspace_id == workspace_id,
                ConversationModel.user_id == user_id,
                ConversationModel.deleted_at.is_(None),
            )
            .order_by(ConversationModel.updated_at.desc(), ConversationModel.created_at.desc())
        ).all()
        return [_conversation_from_model(model) for model in models]


class SQLAlchemyMessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, message: Message) -> None:
        self._session.add(_message_to_model(message))

    def list_for_conversation(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]:
        models = self._session.scalars(
            select(MessageModel)
            .where(
                MessageModel.organization_id == organization_id,
                MessageModel.workspace_id == workspace_id,
                MessageModel.conversation_id == conversation_id,
            )
            .order_by(MessageModel.created_at)
        ).all()
        return [_message_from_model(model) for model in models]


class SQLAlchemyCitationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(self, citations: list[Citation]) -> None:
        self._session.add_all([_citation_to_model(citation) for citation in citations])

    def list_for_message(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        message_id: UUID,
    ) -> list[Citation]:
        models = self._session.scalars(
            select(CitationModel)
            .where(
                CitationModel.organization_id == organization_id,
                CitationModel.workspace_id == workspace_id,
                CitationModel.message_id == message_id,
            )
            .order_by(CitationModel.created_at)
        ).all()
        return [_citation_from_model(model) for model in models]


def _organization_to_model(entity: Organization) -> OrganizationModel:
    return OrganizationModel(
        id=entity.id,
        name=entity.name,
        slug=entity.slug,
        plan=entity.plan,
        status=entity.status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _organization_from_model(model: OrganizationModel) -> Organization:
    return Organization(
        id=model.id,
        name=model.name,
        slug=model.slug,
        plan=model.plan,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _workspace_to_model(entity: Workspace) -> WorkspaceModel:
    return WorkspaceModel(
        id=entity.id,
        organization_id=entity.organization_id,
        name=entity.name,
        slug=entity.slug,
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _workspace_from_model(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        organization_id=model.organization_id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _user_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=entity.email,
        display_name=entity.display_name,
        password_hash=entity.password_hash,
        is_active=entity.is_active,
        email_verified_at=entity.email_verified_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _user_from_model(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        display_name=model.display_name,
        password_hash=model.password_hash,
        is_active=model.is_active,
        email_verified_at=model.email_verified_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _membership_to_model(entity: OrganizationMembership) -> OrganizationMembershipModel:
    return OrganizationMembershipModel(
        id=entity.id,
        organization_id=entity.organization_id,
        user_id=entity.user_id,
        role=entity.role,
        created_at=entity.created_at,
    )


def _membership_from_model(model: OrganizationMembershipModel) -> OrganizationMembership:
    return OrganizationMembership(
        id=model.id,
        organization_id=model.organization_id,
        user_id=model.user_id,
        role=model.role,
        created_at=model.created_at,
    )


def _document_to_model(entity: Document) -> DocumentModel:
    return DocumentModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        owner_user_id=entity.owner_user_id,
        title=entity.title,
        source_type=entity.source_type,
        mime_type=entity.mime_type,
        status=entity.status,
        current_version_id=entity.current_version_id,
        deleted_at=entity.deleted_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _document_from_model(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        owner_user_id=model.owner_user_id,
        title=model.title,
        source_type=model.source_type,
        mime_type=model.mime_type,
        status=model.status,
        current_version_id=model.current_version_id,
        deleted_at=model.deleted_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _document_version_to_model(entity: DocumentVersion) -> DocumentVersionModel:
    return DocumentVersionModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        document_id=entity.document_id,
        version_number=entity.version_number,
        storage_key=entity.storage_key,
        original_filename=entity.original_filename,
        file_sha256=entity.file_sha256,
        size_bytes=entity.size_bytes,
        created_by_user_id=entity.created_by_user_id,
        created_at=entity.created_at,
    )


def _document_version_from_model(model: DocumentVersionModel) -> DocumentVersion:
    return DocumentVersion(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        document_id=model.document_id,
        version_number=model.version_number,
        storage_key=model.storage_key,
        original_filename=model.original_filename,
        file_sha256=model.file_sha256,
        size_bytes=model.size_bytes,
        created_by_user_id=model.created_by_user_id,
        created_at=model.created_at,
    )


def _chunk_to_model(entity: KnowledgeChunk) -> KnowledgeChunkModel:
    return KnowledgeChunkModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        document_id=entity.document_id,
        document_version_id=entity.document_version_id,
        chunk_index=entity.chunk_index,
        content=entity.content,
        content_sha256=entity.content_sha256,
        token_count=entity.token_count,
        created_at=entity.created_at,
    )


def _chunk_from_model(model: KnowledgeChunkModel) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        document_id=model.document_id,
        document_version_id=model.document_version_id,
        chunk_index=model.chunk_index,
        content=model.content,
        content_sha256=model.content_sha256,
        token_count=model.token_count,
        created_at=model.created_at,
    )


def _embedding_to_model(entity: ChunkEmbedding) -> ChunkEmbeddingModel:
    return ChunkEmbeddingModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        chunk_id=entity.chunk_id,
        provider=entity.provider,
        model=entity.model,
        dimensions=entity.dimensions,
        embedding_json=json.dumps(entity.embedding, separators=(",", ":")),
        created_at=entity.created_at,
    )


def _embedding_from_model(model: ChunkEmbeddingModel) -> ChunkEmbedding:
    parsed = json.loads(model.embedding_json)
    embedding = [float(value) for value in parsed]
    return ChunkEmbedding(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        chunk_id=model.chunk_id,
        provider=model.provider,
        model=model.model,
        dimensions=model.dimensions,
        embedding=embedding,
        created_at=model.created_at,
    )


def _conversation_to_model(entity: Conversation) -> ConversationModel:
    return ConversationModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        user_id=entity.user_id,
        title=entity.title,
        status=entity.status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
    )


def _conversation_from_model(model: ConversationModel) -> Conversation:
    return Conversation(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        title=model.title,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def _message_to_model(entity: Message) -> MessageModel:
    return MessageModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        conversation_id=entity.conversation_id,
        role=entity.role,
        content=entity.content,
        created_at=entity.created_at,
    )


def _message_from_model(model: MessageModel) -> Message:
    return Message(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        conversation_id=model.conversation_id,
        role=model.role,
        content=model.content,
        created_at=model.created_at,
    )


def _citation_to_model(entity: Citation) -> CitationModel:
    return CitationModel(
        id=entity.id,
        organization_id=entity.organization_id,
        workspace_id=entity.workspace_id,
        message_id=entity.message_id,
        document_id=entity.document_id,
        document_version_id=entity.document_version_id,
        chunk_id=entity.chunk_id,
        quote=entity.quote,
        score=entity.score,
        created_at=entity.created_at,
    )


def _citation_from_model(model: CitationModel) -> Citation:
    return Citation(
        id=model.id,
        organization_id=model.organization_id,
        workspace_id=model.workspace_id,
        message_id=model.message_id,
        document_id=model.document_id,
        document_version_id=model.document_version_id,
        chunk_id=model.chunk_id,
        quote=model.quote,
        score=model.score,
        created_at=model.created_at,
    )
