"""AI assistant request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import AIMessageRole, Category, Condition


class AIChatRequest(BaseModel):
    """A user turn in the assistant chat."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    conversation_id: uuid.UUID | None = Field(
        None, description="Existing conversation to continue; omit to start a new one"
    )


class AISource(BaseModel):
    """A listing the assistant cited."""

    id: uuid.UUID
    title: str


class AIMessagePublic(BaseModel):
    """A persisted AI conversation message."""

    id: uuid.UUID
    role: AIMessageRole
    content: str
    sources: list[AISource] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationSummary(BaseModel):
    """Conversation list item (no messages)."""

    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationPublic(AIConversationSummary):
    """A conversation with its full message history."""

    messages: list[AIMessagePublic]


class GenerateDescriptionRequest(BaseModel):
    """Inputs for AI listing-description generation."""

    title: str = Field(..., min_length=1, max_length=200, description="Listing title")
    category: Category | None = Field(None, description="Selected category, if any")
    condition: Condition | None = Field(None, description="Selected condition, if any")
    keywords: str | None = Field(
        None, max_length=500, description="Optional seller notes/details to weave in"
    )


class GenerateDescriptionResponse(BaseModel):
    """A generated listing description."""

    description: str
