"""
Pydantic schemas for the AI Privacy Analyst Agent API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Settings schemas
class AgentSettingsResponse(BaseModel):
    """Response schema for agent settings."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    compliance_frameworks: List[str] = Field(default_factory=list)
    custom_system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentSettingsUpdate(BaseModel):
    """Schema for updating agent settings."""

    compliance_frameworks: Optional[List[str]] = None
    custom_system_prompt: Optional[str] = None


# Conversation schemas
class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ConversationResponse(BaseModel):
    """Response schema for a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: Optional[str] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    items: List[ConversationResponse]
    total: int
    page: int
    size: int


# Message schemas
class ToolCallSchema(BaseModel):
    """Schema for a tool call made by the assistant."""

    id: str
    name: str
    arguments: Dict[str, Any]


class MessageResponse(BaseModel):
    """Response schema for a message."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str  # "user", "assistant", or "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    model_used: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    created_at: datetime


class ConversationWithMessagesResponse(BaseModel):
    """Response schema for a conversation with its messages."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: Optional[str] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    """Schema for sending a new message."""

    content: str = Field(..., min_length=1, max_length=32000)


# Embedding schemas
class EmbeddingStats(BaseModel):
    """Statistics about the embedding index."""

    total_embeddings: int
    by_entity_type: Dict[str, int]
    pending_queue_items: int
    oldest_updated_at: Optional[datetime] = None
    newest_updated_at: Optional[datetime] = None


class EmbeddingSyncRequest(BaseModel):
    """Request schema for embedding sync."""

    entity_types: Optional[List[str]] = None


class EmbeddingSyncResponse(BaseModel):
    """Response schema for embedding sync."""

    status: str
    message: str
    entity_types: List[str]
