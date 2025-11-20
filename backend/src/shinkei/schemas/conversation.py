"""Conversation Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ConversationMessageBase(BaseModel):
    """Base conversation message schema."""
    model_config = ConfigDict(populate_by_name=True)

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    reasoning: Optional[str] = None
    message_metadata: Optional[dict] = Field(None, alias="metadata")


class ConversationMessageCreate(ConversationMessageBase):
    """Schema for creating a conversation message."""
    pass


class ConversationMessageResponse(ConversationMessageBase):
    """Schema for conversation message responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    created_at: datetime


class ConversationBase(BaseModel):
    """Base conversation schema."""
    type: str = Field(default="world_chat", pattern="^(world_chat|beat_discussion|story_planning)$")
    title: Optional[str] = None
    context_summary: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    world_id: str
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    model_config = ConfigDict(extra='forbid')

    title: Optional[str] = None
    context_summary: Optional[str] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ConversationMessageResponse]] = []


class ConversationWithMessagesResponse(ConversationResponse):
    """Schema for conversation with recent messages."""
    recent_messages: List[ConversationMessageResponse]


class StreamChunk(BaseModel):
    """Schema for streaming response chunks."""
    chunk: Optional[str] = None
    reasoning: Optional[str] = None
    done: bool = False
    error: Optional[str] = None
