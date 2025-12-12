"""
Message schemas.

This module contains Pydantic models for message request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message (WebSocket only)."""

    content: str = Field(
        ..., min_length=1, max_length=5000, description="Text content of the message"
    )


class MessagePublic(BaseModel):
    """Schema for public message data in API responses."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
