from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.application.unit_of_work import UnitOfWorkFactory
from app.core.errors import AppError
from app.domain.tenancy import ChunkEmbedding, Document, KnowledgeChunk


@dataclass(frozen=True)
class IndexDocumentCommand:
    organization_id: UUID
    workspace_id: UUID
    document_id: UUID


@dataclass(frozen=True)
class IndexDocumentResult:
    document: Document
    chunks_indexed: int
    embeddings_indexed: int
    embedding_provider: str
    embedding_model: str


class DocumentStorageReader(Protocol):
    def get(self, storage_key: str) -> bytes:
        """Read stored document bytes."""


class TextExtractor(Protocol):
    def extract(self, content: bytes, mime_type: str, filename: str) -> str:
        """Extract text from raw document bytes."""


class TextChunker(Protocol):
    def chunk(self, text: str) -> list[str]:
        """Split cleaned text into retrievable chunks."""


class EmbeddingGateway(Protocol):
    @property
    def provider(self) -> str:
        """Embedding provider name."""

    @property
    def model(self) -> str:
        """Embedding model name."""

    @property
    def dimensions(self) -> int:
        """Embedding vector dimensions."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for text chunks."""


@dataclass(frozen=True)
class IndexingService:
    uow_factory: UnitOfWorkFactory
    storage: DocumentStorageReader
    extractor: TextExtractor
    chunker: TextChunker
    embedding_gateway: EmbeddingGateway

    def index_document(self, command: IndexDocumentCommand) -> IndexDocumentResult:
        now = _utc_now()
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
            if document.current_version_id is None:
                raise AppError(
                    code="document.version_missing",
                    message="Document has no current version to index.",
                    status_code=409,
                    details={"document_id": str(document.id)},
                )

            version = uow.document_versions.get(document.current_version_id)
            if version is None:
                raise AppError(
                    code="document.version_missing",
                    message="Document version not found.",
                    status_code=409,
                    details={"version_id": str(document.current_version_id)},
                )

            raw_content = self.storage.get(version.storage_key)
            extracted_text = self.extractor.extract(
                raw_content,
                document.mime_type,
                version.original_filename,
            )
            cleaned_text = clean_text(extracted_text)
            chunk_texts = self.chunker.chunk(cleaned_text)
            if not chunk_texts:
                raise AppError(
                    code="document.no_indexable_text",
                    message="Document did not contain indexable text.",
                    status_code=422,
                    details={"document_id": str(document.id)},
                )

            uow.embeddings.delete_for_document_version(version.id)
            uow.chunks.delete_for_document_version(version.id)

            chunks = [
                KnowledgeChunk(
                    id=uuid4(),
                    organization_id=document.organization_id,
                    workspace_id=document.workspace_id,
                    document_id=document.id,
                    document_version_id=version.id,
                    chunk_index=index,
                    content=chunk_text,
                    content_sha256=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                    token_count=len(chunk_text.split()),
                    created_at=now,
                )
                for index, chunk_text in enumerate(chunk_texts)
            ]
            vectors = self.embedding_gateway.embed([chunk.content for chunk in chunks])
            if len(vectors) != len(chunks):
                raise AppError(
                    code="embedding.count_mismatch",
                    message="Embedding provider returned an unexpected number of vectors.",
                    status_code=502,
                    details={"chunks": len(chunks), "vectors": len(vectors)},
                )
            embeddings = [
                ChunkEmbedding(
                    id=uuid4(),
                    organization_id=chunk.organization_id,
                    workspace_id=chunk.workspace_id,
                    chunk_id=chunk.id,
                    provider=self.embedding_gateway.provider,
                    model=self.embedding_gateway.model,
                    dimensions=self.embedding_gateway.dimensions,
                    embedding=vector,
                    created_at=now,
                )
                for chunk, vector in (
                    (chunks[index], vectors[index]) for index in range(len(chunks))
                )
            ]
            indexed_document = _replace_document_status(document, "indexed", now)

            uow.chunks.add_many(chunks)
            uow.embeddings.add_many(embeddings)
            uow.documents.update(indexed_document)
            uow.commit()

        return IndexDocumentResult(
            document=indexed_document,
            chunks_indexed=len(chunks),
            embeddings_indexed=len(embeddings),
            embedding_provider=self.embedding_gateway.provider,
            embedding_model=self.embedding_gateway.model,
        )

    def list_chunks(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        document_id: UUID,
    ) -> list[KnowledgeChunk]:
        with self.uow_factory() as uow:
            document = uow.documents.get(organization_id, workspace_id, document_id)
            if document is None:
                raise AppError(
                    code="document.not_found",
                    message="Document not found.",
                    status_code=404,
                    details={"document_id": str(document_id)},
                )
            return uow.chunks.list_for_document(organization_id, workspace_id, document_id)


class PlainTextExtractor:
    _supported_mime_types = {
        "text/markdown",
        "text/plain",
        "text/html",
        "text/csv",
        "application/json",
    }

    def extract(self, content: bytes, mime_type: str, filename: str) -> str:
        if mime_type not in self._supported_mime_types:
            raise AppError(
                code="document.extraction_not_supported",
                message="Text extraction for this file type is not implemented yet.",
                status_code=422,
                details={"mime_type": mime_type, "filename": filename},
            )

        text = content.decode("utf-8", errors="replace")
        if mime_type == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)
            text = html.unescape(text)
        return text


@dataclass(frozen=True)
class FixedWindowChunker:
    max_words: int = 180
    overlap_words: int = 30

    def chunk(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        step = max(1, self.max_words - self.overlap_words)
        for start in range(0, len(words), step):
            chunk_words = words[start : start + self.max_words]
            if chunk_words:
                chunks.append(" ".join(chunk_words))
            if start + self.max_words >= len(words):
                break
        return chunks


@dataclass(frozen=True)
class DeterministicEmbeddingGateway:
    provider: str = "local"
    model: str = "deterministic-hash-embedding"
    dimensions: int = 16

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(self.dimensions):
            raw = digest[index] / 255
            values.append(round((raw * 2) - 1, 6))
        return values


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _replace_document_status(document: Document, status: str, updated_at: datetime) -> Document:
    return Document(
        id=document.id,
        organization_id=document.organization_id,
        workspace_id=document.workspace_id,
        owner_user_id=document.owner_user_id,
        title=document.title,
        source_type=document.source_type,
        mime_type=document.mime_type,
        status=status,
        current_version_id=document.current_version_id,
        deleted_at=document.deleted_at,
        created_at=document.created_at,
        updated_at=updated_at,
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017
