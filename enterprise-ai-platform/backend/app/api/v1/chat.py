from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.chat import AskQuestionCommand, ChatAnswerResult, ChatMessage, ChatService
from app.core.container import AppContainer
from app.schemas.chat import (
    ChatCitationResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationTranscriptResponse,
)

router = APIRouter(prefix="/organizations/{organization_id}/workspaces/{workspace_id}/chat")


@router.post("", response_model=ChatResponse, summary="Ask grounded chat")
async def ask_chat(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    payload: ChatRequest,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> ChatResponse:
    auth_service.require_permission(session, organization_id, "documents.search")
    service = _chat_service(request)
    result = service.ask(
        AskQuestionCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_user_id=session.user.id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            top_k=payload.top_k,
        )
    )
    return _chat_response(result)


@router.get(
    "/history",
    response_model=list[ConversationResponse],
    summary="List chat conversations",
)
async def list_chat_history(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> list[ConversationResponse]:
    auth_service.require_permission(session, organization_id, "documents.search")
    service = _chat_service(request)
    return [
        ConversationResponse.model_validate(conversation)
        for conversation in service.list_conversations(
            organization_id,
            workspace_id,
            session.user.id,
        )
    ]


@router.get(
    "/{conversation_id}",
    response_model=ConversationTranscriptResponse,
    summary="Get chat transcript",
)
async def get_chat_transcript(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    conversation_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> ConversationTranscriptResponse:
    auth_service.require_permission(session, organization_id, "documents.search")
    service = _chat_service(request)
    transcript = service.get_transcript(
        organization_id,
        workspace_id,
        session.user.id,
        conversation_id,
    )
    return ConversationTranscriptResponse(
        conversation=ConversationResponse.model_validate(transcript.conversation),
        messages=[_message_response(message) for message in transcript.messages],
    )


def _chat_service(request: Request) -> ChatService:
    container: AppContainer = request.app.state.container
    return container.chat_service


def _chat_response(result: ChatAnswerResult) -> ChatResponse:
    citations = [
        ChatCitationResponse(
            id=citation.id,
            document_id=citation.document_id,
            document_version_id=citation.document_version_id,
            chunk_id=citation.chunk_id,
            quote=citation.quote,
            score=citation.score,
        )
        for citation in result.citations
    ]
    return ChatResponse(
        conversation=ConversationResponse.model_validate(result.conversation),
        user_message=ChatMessageResponse(
            id=result.user_message.id,
            role=result.user_message.role,
            content=result.user_message.content,
            created_at=result.user_message.created_at,
            citations=[],
        ),
        assistant_message=ChatMessageResponse(
            id=result.assistant_message.id,
            role=result.assistant_message.role,
            content=result.assistant_message.content,
            created_at=result.assistant_message.created_at,
            citations=citations,
        ),
        citations=citations,
    )


def _message_response(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        citations=[
            ChatCitationResponse(
                id=citation.id,
                document_id=citation.document_id,
                document_version_id=citation.document_version_id,
                chunk_id=citation.chunk_id,
                quote=citation.quote,
                score=citation.score,
            )
            for citation in message.citations
        ],
    )
