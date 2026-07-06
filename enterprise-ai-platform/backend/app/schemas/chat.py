from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[UUID] = None  # noqa: UP045
    top_k: int = Field(default=5, ge=1, le=10)


class ChatCitationResponse(BaseModel):
    id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    quote: str
    score: float


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    citations: list[ChatCitationResponse]


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    workspace_id: UUID
    user_id: UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChatResponse(BaseModel):
    conversation: ConversationResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    citations: list[ChatCitationResponse]


class ConversationTranscriptResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[ChatMessageResponse]
