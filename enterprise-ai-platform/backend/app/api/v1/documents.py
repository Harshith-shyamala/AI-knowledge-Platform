from __future__ import annotations

from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, Request, UploadFile, status

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.documents import (
    DocumentService,
    UploadDocumentCommand,
    UploadDocumentVersionCommand,
    UploadedFilePayload,
)
from app.application.indexing import IndexDocumentCommand, IndexDocumentResult, IndexingService
from app.core.container import AppContainer
from app.schemas.documents import (
    ChunkResponse,
    DocumentResponse,
    DocumentVersionResponse,
    IndexDocumentResponse,
    UploadDocumentResponse,
)

router = APIRouter(prefix="/organizations/{organization_id}/workspaces/{workspace_id}/documents")


@router.post(
    "",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
)
async def upload_document(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
    file: Annotated[UploadFile, File()],
    title: Annotated[Optional[str], Form()] = None,  # noqa: UP045
) -> UploadDocumentResponse:
    auth_service.require_permission(session, organization_id, "documents.upload")
    service = _document_service(request)
    result = service.upload_document(
        UploadDocumentCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_user_id=session.user.id,
            title=title,
            file=UploadedFilePayload(
                filename=file.filename or "",
                content_type=file.content_type or "application/octet-stream",
                content=await file.read(),
            ),
        )
    )
    return _upload_response(result)


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List documents",
)
async def list_documents(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> list[DocumentResponse]:
    auth_service.require_permission(session, organization_id, "documents.read")
    service = _document_service(request)
    return [
        DocumentResponse.model_validate(document)
        for document in service.list_documents(organization_id, workspace_id)
    ]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
)
async def get_document(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> DocumentResponse:
    auth_service.require_permission(session, organization_id, "documents.read")
    service = _document_service(request)
    return DocumentResponse.model_validate(
        service.get_document(organization_id, workspace_id, document_id)
    )


@router.post(
    "/{document_id}/versions",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document version",
)
async def upload_document_version(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
    file: Annotated[UploadFile, File()],
) -> UploadDocumentResponse:
    auth_service.require_permission(session, organization_id, "documents.upload")
    service = _document_service(request)
    result = service.upload_document_version(
        UploadDocumentVersionCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            document_id=document_id,
            actor_user_id=session.user.id,
            file=UploadedFilePayload(
                filename=file.filename or "",
                content_type=file.content_type or "application/octet-stream",
                content=await file.read(),
            ),
        )
    )
    return _upload_response(result)


@router.get(
    "/{document_id}/versions",
    response_model=list[DocumentVersionResponse],
    summary="List document versions",
)
async def list_document_versions(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> list[DocumentVersionResponse]:
    auth_service.require_permission(session, organization_id, "documents.read")
    service = _document_service(request)
    return [
        DocumentVersionResponse.model_validate(version)
        for version in service.list_versions(organization_id, workspace_id, document_id)
    ]


@router.post(
    "/{document_id}/index",
    response_model=IndexDocumentResponse,
    summary="Index document",
)
async def index_document(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> IndexDocumentResponse:
    auth_service.require_permission(session, organization_id, "documents.upload")
    service = _indexing_service(request)
    result = service.index_document(
        IndexDocumentCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            document_id=document_id,
        )
    )
    return _index_response(result)


@router.get(
    "/{document_id}/chunks",
    response_model=list[ChunkResponse],
    summary="List document chunks",
)
async def list_document_chunks(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> list[ChunkResponse]:
    auth_service.require_permission(session, organization_id, "documents.read")
    service = _indexing_service(request)
    return [
        ChunkResponse.model_validate(chunk)
        for chunk in service.list_chunks(organization_id, workspace_id, document_id)
    ]


def _document_service(request: Request) -> DocumentService:
    container: AppContainer = request.app.state.container
    return container.document_service


def _indexing_service(request: Request) -> IndexingService:
    container: AppContainer = request.app.state.container
    return container.indexing_service


def _upload_response(result: Any) -> UploadDocumentResponse:
    return UploadDocumentResponse(
        document=DocumentResponse.model_validate(result.document),
        version=DocumentVersionResponse.model_validate(result.version),
        job_id=result.job_id,
        duplicate_hint=result.duplicate_hint,
    )


def _index_response(result: IndexDocumentResult) -> IndexDocumentResponse:
    return IndexDocumentResponse(
        document=DocumentResponse.model_validate(result.document),
        chunks_indexed=result.chunks_indexed,
        embeddings_indexed=result.embeddings_indexed,
        embedding_provider=result.embedding_provider,
        embedding_model=result.embedding_model,
    )
