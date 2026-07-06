from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Protocol
from uuid import UUID, uuid4

from app.application.unit_of_work import UnitOfWorkFactory
from app.core.config import Settings
from app.core.errors import AppError
from app.domain.tenancy import Document, DocumentVersion

_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class UploadedFilePayload:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class UploadDocumentCommand:
    organization_id: UUID
    workspace_id: UUID
    actor_user_id: UUID
    title: str | None
    file: UploadedFilePayload


@dataclass(frozen=True)
class UploadDocumentVersionCommand:
    organization_id: UUID
    workspace_id: UUID
    document_id: UUID
    actor_user_id: UUID
    file: UploadedFilePayload


@dataclass(frozen=True)
class UploadDocumentResult:
    document: Document
    version: DocumentVersion
    job_id: UUID
    duplicate_hint: bool


class DocumentStorage(Protocol):
    def put(self, storage_key: str, content: bytes) -> None:
        """Store file content."""


@dataclass(frozen=True)
class DocumentService:
    uow_factory: UnitOfWorkFactory
    storage: DocumentStorage
    settings: Settings

    def upload_document(self, command: UploadDocumentCommand) -> UploadDocumentResult:
        validated = self._validate(command.file)
        now = _utc_now()
        document_id = uuid4()
        version_id = uuid4()
        title = (command.title or _title_from_filename(command.file.filename)).strip()
        storage_key = _storage_key(
            command.organization_id,
            command.workspace_id,
            document_id,
            version_id,
            command.file.filename,
        )
        document = Document(
            id=document_id,
            organization_id=command.organization_id,
            workspace_id=command.workspace_id,
            owner_user_id=command.actor_user_id,
            title=title,
            source_type="upload",
            mime_type=validated.mime_type,
            status="uploaded",
            current_version_id=version_id,
            deleted_at=None,
            created_at=now,
            updated_at=now,
        )
        version = DocumentVersion(
            id=version_id,
            organization_id=command.organization_id,
            workspace_id=command.workspace_id,
            document_id=document_id,
            version_number=1,
            storage_key=storage_key,
            original_filename=command.file.filename,
            file_sha256=validated.file_sha256,
            size_bytes=validated.size_bytes,
            created_by_user_id=command.actor_user_id,
            created_at=now,
        )

        with self.uow_factory() as uow:
            workspace = uow.workspaces.get(command.organization_id, command.workspace_id)
            if workspace is None:
                raise AppError(
                    code="workspace.not_found",
                    message="Workspace not found.",
                    status_code=404,
                    details={
                        "organization_id": str(command.organization_id),
                        "workspace_id": str(command.workspace_id),
                    },
                )

            uow.documents.add(document)
            uow.document_versions.add(version)
            self.storage.put(storage_key, command.file.content)
            uow.commit()

        return UploadDocumentResult(
            document=document,
            version=version,
            job_id=uuid4(),
            duplicate_hint=False,
        )

    def upload_document_version(
        self,
        command: UploadDocumentVersionCommand,
    ) -> UploadDocumentResult:
        validated = self._validate(command.file)
        now = _utc_now()
        version_id = uuid4()

        with self.uow_factory() as uow:
            document = uow.documents.get(
                command.organization_id,
                command.workspace_id,
                command.document_id,
            )
            if document is None:
                raise AppError(
                    code="document.not_found",
                    message="Document not found.",
                    status_code=404,
                    details={"document_id": str(command.document_id)},
                )

            version_number = uow.document_versions.latest_version_number(document.id) + 1
            storage_key = _storage_key(
                command.organization_id,
                command.workspace_id,
                document.id,
                version_id,
                command.file.filename,
            )
            version = DocumentVersion(
                id=version_id,
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                document_id=document.id,
                version_number=version_number,
                storage_key=storage_key,
                original_filename=command.file.filename,
                file_sha256=validated.file_sha256,
                size_bytes=validated.size_bytes,
                created_by_user_id=command.actor_user_id,
                created_at=now,
            )
            updated_document = Document(
                id=document.id,
                organization_id=document.organization_id,
                workspace_id=document.workspace_id,
                owner_user_id=document.owner_user_id,
                title=document.title,
                source_type=document.source_type,
                mime_type=validated.mime_type,
                status="uploaded",
                current_version_id=version.id,
                deleted_at=document.deleted_at,
                created_at=document.created_at,
                updated_at=now,
            )

            uow.document_versions.add(version)
            uow.documents.update(updated_document)
            self.storage.put(storage_key, command.file.content)
            uow.commit()

        return UploadDocumentResult(
            document=updated_document,
            version=version,
            job_id=uuid4(),
            duplicate_hint=False,
        )

    def list_documents(self, organization_id: UUID, workspace_id: UUID) -> list[Document]:
        with self.uow_factory() as uow:
            return uow.documents.list_for_workspace(organization_id, workspace_id)

    def get_document(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        document_id: UUID,
    ) -> Document:
        with self.uow_factory() as uow:
            document = uow.documents.get(organization_id, workspace_id, document_id)

        if document is None:
            raise AppError(
                code="document.not_found",
                message="Document not found.",
                status_code=404,
                details={"document_id": str(document_id)},
            )
        return document

    def list_versions(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        document_id: UUID,
    ) -> list[DocumentVersion]:
        with self.uow_factory() as uow:
            document = uow.documents.get(organization_id, workspace_id, document_id)
            if document is None:
                raise AppError(
                    code="document.not_found",
                    message="Document not found.",
                    status_code=404,
                    details={"document_id": str(document_id)},
                )
            return uow.document_versions.list_for_document(document_id)

    def _validate(self, file: UploadedFilePayload) -> ValidatedUpload:
        if not file.filename.strip():
            raise AppError(
                code="document.filename_required",
                message="Uploaded file must have a filename.",
                status_code=422,
                details={},
            )
        if not file.content:
            raise AppError(
                code="document.empty_file",
                message="Uploaded file is empty.",
                status_code=422,
                details={},
            )
        if len(file.content) > self.settings.max_upload_size_bytes:
            raise AppError(
                code="document.file_too_large",
                message="Uploaded file exceeds the configured size limit.",
                status_code=413,
                details={"max_upload_size_bytes": self.settings.max_upload_size_bytes},
            )

        extension = PurePosixPath(file.filename).suffix.lower()
        mime_type = (
            (file.content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
        )
        normalized_mime_type = _normalize_mime_type(extension, mime_type)
        if extension not in _ALLOWED_EXTENSIONS or normalized_mime_type is None:
            raise AppError(
                code="document.unsupported_file_type",
                message="The uploaded file type is not supported.",
                status_code=415,
                details={"extension": extension, "mime_type": mime_type},
            )

        return ValidatedUpload(
            mime_type=normalized_mime_type,
            file_sha256=hashlib.sha256(file.content).hexdigest(),
            size_bytes=len(file.content),
        )


@dataclass(frozen=True)
class ValidatedUpload:
    mime_type: str
    file_sha256: str
    size_bytes: int


def _storage_key(
    organization_id: UUID,
    workspace_id: UUID,
    document_id: UUID,
    version_id: UUID,
    filename: str,
) -> str:
    return "/".join(
        [
            str(organization_id),
            str(workspace_id),
            str(document_id),
            f"{version_id}-{_safe_filename(filename)}",
        ]
    )


def _safe_filename(filename: str) -> str:
    cleaned = _SAFE_FILENAME_PATTERN.sub("-", PurePosixPath(filename).name).strip(".-")
    return cleaned or "upload.bin"


def _title_from_filename(filename: str) -> str:
    name = PurePosixPath(filename).name
    suffix = PurePosixPath(filename).suffix
    return name[: -len(suffix)] if suffix else name


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017


def _normalize_mime_type(extension: str, mime_type: str) -> str | None:
    mime_type = _MIME_TYPE_ALIASES.get(mime_type, mime_type)
    if mime_type in _ALLOWED_MIME_TYPES:
        if extension in _TEXT_EXTENSIONS:
            return _MIME_TYPE_BY_EXTENSION[extension]
        return mime_type
    if mime_type in _GENERIC_MIME_TYPES or mime_type.startswith("text/"):
        return _MIME_TYPE_BY_EXTENSION.get(extension)
    return None


_ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".md",
    ".txt",
    ".html",
    ".htm",
    ".csv",
    ".json",
}

_ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/markdown",
    "text/plain",
    "text/html",
    "text/csv",
    "application/json",
}

_GENERIC_MIME_TYPES = {
    "",
    "application/octet-stream",
    "binary/octet-stream",
}

_MIME_TYPE_ALIASES = {
    "application/markdown": "text/markdown",
    "application/x-markdown": "text/markdown",
    "application/x-md": "text/markdown",
    "text/md": "text/markdown",
    "text/x-markdown": "text/markdown",
    "text/json": "application/json",
}

_MIME_TYPE_BY_EXTENSION = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".csv": "text/csv",
    ".json": "application/json",
}

_TEXT_EXTENSIONS = frozenset(_MIME_TYPE_BY_EXTENSION)
