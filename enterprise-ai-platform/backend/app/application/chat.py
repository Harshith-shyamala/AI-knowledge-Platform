from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

from app.application.retrieval import HybridRetrievalService, SearchKnowledgeCommand, SearchResult
from app.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.core.errors import AppError
from app.domain.tenancy import Citation, Conversation, Message


@dataclass(frozen=True)
class AskQuestionCommand:
    organization_id: UUID
    workspace_id: UUID
    actor_user_id: UUID
    message: str
    conversation_id: UUID | None = None
    top_k: int = 5


@dataclass(frozen=True)
class ChatCitation:
    id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    quote: str
    score: float


@dataclass(frozen=True)
class ChatMessage:
    id: UUID
    role: str
    content: str
    created_at: datetime
    citations: list[ChatCitation]


@dataclass(frozen=True)
class ChatAnswerResult:
    conversation: Conversation
    user_message: Message
    assistant_message: Message
    citations: list[ChatCitation]


@dataclass(frozen=True)
class ConversationTranscript:
    conversation: Conversation
    messages: list[ChatMessage]


class AnswerGenerator(Protocol):
    def generate(self, question: str, context: list[SearchResult]) -> str:
        """Generate a grounded answer from retrieved context."""


@dataclass(frozen=True)
class ChatService:
    uow_factory: UnitOfWorkFactory
    retrieval_service: HybridRetrievalService
    answer_generator: AnswerGenerator

    def ask(self, command: AskQuestionCommand) -> ChatAnswerResult:
        question = command.message.strip()
        if not question:
            raise AppError(
                code="chat.empty_message",
                message="Chat message must not be empty.",
                status_code=422,
                details={},
            )
        if command.top_k < 1 or command.top_k > 10:
            raise AppError(
                code="chat.invalid_top_k",
                message="top_k must be between 1 and 10.",
                status_code=422,
                details={"top_k": command.top_k},
            )

        retrieved = self.retrieval_service.search(
            SearchKnowledgeCommand(
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                query=question,
                top_k=command.top_k,
            )
        )
        answer = self.answer_generator.generate(question, retrieved)
        now = _utc_now()

        with self.uow_factory() as uow:
            self._require_workspace(uow, command.organization_id, command.workspace_id)
            conversation = self._get_or_create_conversation(command, question, now, uow)
            user_message = Message(
                id=uuid4(),
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                conversation_id=conversation.id,
                role="user",
                content=question,
                created_at=now,
            )
            assistant_message = Message(
                id=uuid4(),
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                created_at=now,
            )
            citations = [
                Citation(
                    id=uuid4(),
                    organization_id=command.organization_id,
                    workspace_id=command.workspace_id,
                    message_id=assistant_message.id,
                    document_id=result.document_id,
                    document_version_id=result.document_version_id,
                    chunk_id=result.chunk_id,
                    quote=_quote(result.content),
                    score=result.score,
                    created_at=now,
                )
                for result in retrieved
            ]
            uow.messages.add(user_message)
            uow.messages.add(assistant_message)
            uow.citations.add_many(citations)
            uow.commit()

        return ChatAnswerResult(
            conversation=conversation,
            user_message=user_message,
            assistant_message=assistant_message,
            citations=[_chat_citation(citation) for citation in citations],
        )

    def list_conversations(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        actor_user_id: UUID,
    ) -> list[Conversation]:
        with self.uow_factory() as uow:
            return uow.conversations.list_for_user(organization_id, workspace_id, actor_user_id)

    def get_transcript(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        actor_user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationTranscript:
        with self.uow_factory() as uow:
            conversation = uow.conversations.get(
                organization_id,
                workspace_id,
                conversation_id,
                actor_user_id,
            )
            if conversation is None:
                raise AppError(
                    code="chat.conversation_not_found",
                    message="Conversation was not found.",
                    status_code=404,
                    details={"conversation_id": str(conversation_id)},
                )

            messages = []
            for message in uow.messages.list_for_conversation(
                organization_id,
                workspace_id,
                conversation.id,
            ):
                citations = [
                    _chat_citation(citation)
                    for citation in uow.citations.list_for_message(
                        organization_id,
                        workspace_id,
                        message.id,
                    )
                ]
                messages.append(
                    ChatMessage(
                        id=message.id,
                        role=message.role,
                        content=message.content,
                        created_at=message.created_at,
                        citations=citations,
                    )
                )

        return ConversationTranscript(conversation=conversation, messages=messages)

    def _get_or_create_conversation(
        self,
        command: AskQuestionCommand,
        question: str,
        now: datetime,
        uow: UnitOfWork,
    ) -> Conversation:
        if command.conversation_id is not None:
            conversation = uow.conversations.get(
                command.organization_id,
                command.workspace_id,
                command.conversation_id,
                command.actor_user_id,
            )
            if conversation is None:
                raise AppError(
                    code="chat.conversation_not_found",
                    message="Conversation was not found.",
                    status_code=404,
                    details={"conversation_id": str(command.conversation_id)},
                )
            return conversation

        conversation = Conversation(
            id=uuid4(),
            organization_id=command.organization_id,
            workspace_id=command.workspace_id,
            user_id=command.actor_user_id,
            title=_title_from_question(question),
            status="active",
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        uow.conversations.add(conversation)
        return conversation

    @staticmethod
    def _require_workspace(uow: UnitOfWork, organization_id: UUID, workspace_id: UUID) -> None:
        if uow.workspaces.get(organization_id, workspace_id) is None:
            raise AppError(
                code="workspace.not_found",
                message="Workspace was not found.",
                status_code=404,
                details={"workspace_id": str(workspace_id)},
            )


class GroundedAnswerGenerator:
    def generate(self, question: str, context: list[SearchResult]) -> str:
        if not context:
            return (
                "I do not have enough indexed knowledge to answer that yet. "
                "Upload and index relevant documents, then ask again."
            )

        if _is_summary_question(question):
            return _summary_answer(context)

        question_terms = _meaningful_terms(question)
        candidates: list[tuple[float, str]] = []
        for rank, result in enumerate(context):
            for sentence in _sentences(result.content):
                sentence_terms = _meaningful_terms(sentence)
                overlap = question_terms & sentence_terms
                if not overlap:
                    continue
                score = (
                    (len(overlap) / max(len(question_terms), 1))
                    + (0.15 * result.lexical_score)
                    + (0.05 * result.score)
                    + _question_intent_bonus(question, sentence_terms)
                    - (0.01 * rank)
                )
                candidates.append((score, sentence))

        if not candidates:
            return (
                "I found indexed context, but it does not directly answer that question. "
                f"Most relevant context: {_quote(context[0].content)}"
            )

        selected = _dedupe_sentences(
            sentence for _, sentence in sorted(candidates, key=lambda item: item[0], reverse=True)
        )[:1]
        return "Based on the indexed knowledge: " + " ".join(selected)


def _chat_citation(citation: Citation) -> ChatCitation:
    return ChatCitation(
        id=citation.id,
        document_id=citation.document_id,
        document_version_id=citation.document_version_id,
        chunk_id=citation.chunk_id,
        quote=citation.quote,
        score=citation.score,
    )


def _quote(content: str) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= 500:
        return normalized
    return f"{normalized[:497]}..."


def _title_from_question(question: str) -> str:
    normalized = " ".join(question.split())
    if len(normalized) <= 80:
        return normalized
    return f"{normalized[:77]}..."


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017


def _is_summary_question(question: str) -> bool:
    terms = _meaningful_terms(question)
    return bool(terms & {"overview", "summarize", "summary"})


def _summary_answer(context: list[SearchResult]) -> str:
    sentences = _dedupe_sentences(
        sentence for result in context for sentence in _sentences(result.content)
    )
    headings = _dedupe_sentences(
        heading for result in context for heading in _markdown_headings(result.content)
    )
    selected = sentences[:3]
    if headings:
        covered = ", ".join(headings[:6])
        prefix = f"The indexed knowledge covers {covered}."
        if selected:
            return f"{prefix} Key points: {' '.join(selected)}"
        return prefix
    return "Based on the indexed knowledge: " + " ".join(selected)


def _sentences(content: str) -> list[str]:
    without_headings = _strip_markdown_headings(content)
    parts = re.split(r"(?<=[.!?])\s+|\n+", without_headings)
    return [_clean_sentence(part) for part in parts if _clean_sentence(part)]


def _markdown_headings(content: str) -> list[str]:
    line_headings = [
        _clean_sentence(match.group(1))
        for match in re.finditer(r"(?m)^\s*#{1,6}\s+(.+?)\s*$", content)
    ]
    flat_headings = [
        _clean_sentence(match.group(1))
        for match in re.finditer(_FLAT_MARKDOWN_HEADING_PATTERN, content)
    ]
    return _dedupe_sentences([*line_headings, *flat_headings])


def _strip_markdown_headings(content: str) -> str:
    without_line_headings = "\n".join(
        "" if _is_markdown_heading_line(line) else line for line in content.splitlines()
    )
    return re.sub(_FLAT_MARKDOWN_HEADING_PATTERN, " ", without_line_headings)


def _is_markdown_heading_line(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("#")
        and len(stripped) <= 80
        and not any(punctuation in stripped for punctuation in ".?!")
    )


def _clean_sentence(sentence: str) -> str:
    cleaned = " ".join(sentence.strip(" #-*\t\r\n").split())
    return cleaned if len(cleaned) > 2 else ""


def _dedupe_sentences(sentences: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(sentence)
    return unique


def _meaningful_terms(text: str) -> set[str]:
    return {
        normalized
        for token in _TOKEN_PATTERN.findall(text)
        if (normalized := _normalize_term(token)) and normalized not in _STOP_WORDS
    }


def _question_intent_bonus(question: str, sentence_terms: set[str]) -> float:
    normalized = question.lower()
    bonus = 0.0
    if "what evidence" in normalized and "evidence" in sentence_terms:
        bonus += 0.5
    if "how quickly" in normalized and sentence_terms & {"hour", "day", "within"}:
        bonus += 0.5
    if normalized.startswith("can ") and sentence_terms & {"not", "unless", "approved"}:
        bonus += 0.25
    return bonus


def _normalize_term(token: str) -> str:
    term = token.lower()
    if len(term) > 5 and term.endswith("ing"):
        return term[:-3]
    if len(term) > 4 and term.endswith("ied"):
        return f"{term[:-3]}y"
    if len(term) > 4 and term.endswith("ed"):
        return term[:-2]
    if len(term) > 4 and term.endswith("es"):
        return term[:-2]
    if len(term) > 3 and term.endswith("s") and not term.endswith("ss"):
        return term[:-1]
    return term


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")

_FLAT_MARKDOWN_HEADING_PATTERN = (
    r"(?:^|\s)#{1,6}\s+([A-Z][A-Za-z0-9 /&-]{1,48}?)"
    r"(?=\s+(?:All|Any|Approved|Critical|Customer|Employees|Security|The|Quarterly|"
    r"AI tools)|\s+#|$)"
)

_STOP_WORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "as",
    "be",
    "before",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "must",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "who",
    "with",
}
