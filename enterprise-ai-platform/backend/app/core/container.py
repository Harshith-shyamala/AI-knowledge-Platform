from __future__ import annotations

from dataclasses import dataclass

from app.application.agents import AgentWorkflowService
from app.application.auth import AuthService
from app.application.chat import ChatService, GroundedAnswerGenerator
from app.application.documents import DocumentService
from app.application.evaluation import EvaluationService, default_evaluators
from app.application.health import HealthService, StaticReadinessProbe
from app.application.indexing import (
    DeterministicEmbeddingGateway,
    FixedWindowChunker,
    IndexingService,
    PlainTextExtractor,
)
from app.application.organizations import OrganizationService
from app.application.retrieval import HybridRetrievalService, ScoreReranker
from app.application.security import JwtTokenService, PasswordHasher, RbacPolicy
from app.application.unit_of_work import UnitOfWork
from app.core.config import Settings
from app.core.ports import ReadinessProbe
from app.infrastructure.persistence.database import (
    DatabaseReadinessProbe,
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.storage import LocalDocumentStorage


@dataclass(frozen=True)
class AppContainer:
    """Small dependency container for application services.

    This keeps construction in one place now and gives later milestones a clear home
    for repositories, units of work, gateways, queues, and observability adapters.
    """

    settings: Settings
    health_service: HealthService
    organization_service: OrganizationService
    auth_service: AuthService
    document_service: DocumentService
    indexing_service: IndexingService
    retrieval_service: HybridRetrievalService
    chat_service: ChatService
    agent_workflow_service: AgentWorkflowService
    evaluation_service: EvaluationService

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        engine = create_database_engine(settings)
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)

        session_factory = create_session_factory(engine)
        probes: tuple[ReadinessProbe, ...] = (
            StaticReadinessProbe("api-process"),
            DatabaseReadinessProbe(session_factory),
        )

        def uow_factory() -> UnitOfWork:
            return SQLAlchemyUnitOfWork(session_factory)

        storage = LocalDocumentStorage(settings.storage_root)

        embedding_gateway = DeterministicEmbeddingGateway()

        retrieval_service = HybridRetrievalService(
            uow_factory=uow_factory,
            embedding_gateway=embedding_gateway,
            reranker=ScoreReranker(),
        )

        answer_generator = GroundedAnswerGenerator()
        agent_workflow_service = AgentWorkflowService(
            uow_factory=uow_factory,
            retrieval_service=retrieval_service,
            answer_generator=answer_generator,
        )

        return cls(
            settings=settings,
            health_service=HealthService(settings=settings, readiness_probes=probes),
            organization_service=OrganizationService(uow_factory=uow_factory),
            auth_service=AuthService(
                uow_factory=uow_factory,
                password_hasher=PasswordHasher(),
                token_service=JwtTokenService(settings),
                rbac_policy=RbacPolicy(),
            ),
            document_service=DocumentService(
                uow_factory=uow_factory,
                storage=storage,
                settings=settings,
            ),
            indexing_service=IndexingService(
                uow_factory=uow_factory,
                storage=storage,
                extractor=PlainTextExtractor(),
                chunker=FixedWindowChunker(),
                embedding_gateway=embedding_gateway,
            ),
            retrieval_service=retrieval_service,
            chat_service=ChatService(
                uow_factory=uow_factory,
                retrieval_service=retrieval_service,
                answer_generator=answer_generator,
            ),
            agent_workflow_service=agent_workflow_service,
            evaluation_service=EvaluationService(
                agent_workflow_service=agent_workflow_service,
                evaluators=default_evaluators(),
            ),
        )
