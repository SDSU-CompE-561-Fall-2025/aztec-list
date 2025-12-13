"""
Message schemas.

This module contains Pydantic models for message request/response validation.
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MessageCreate(BaseModel):
    """Schema for creating a new message (WebSocket only)."""

    content: str = Field(
        ..., min_length=1, max_length=5000, description="Text content of the message"
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """
        Sanitize message content to prevent XSS attacks while preserving normal text.

        - Rejects content with HTML tags (< followed by letters)
        - Removes javascript: and data: protocols
        - Preserves all normal characters, punctuation, emojis, and line breaks
        - Frontend must handle proper escaping when displaying
        """
        if not v:
            return v

        # Remove javascript: protocols
        sanitized = re.sub(r"javascript\s*:", "", v, flags=re.IGNORECASE)

        # Remove data: URIs
        sanitized = re.sub(r"data\s*:", "", sanitized, flags=re.IGNORECASE)

        # Check for HTML tags - reject if found
        # Matches < followed by letter (opening tags) or </ (closing tags)
        if re.search(r"<\s*/?\s*[a-zA-Z]", sanitized):
            msg = "Message content cannot contain HTML tags. Please use plain text."
            raise ValueError(msg)

        return sanitized.strip()


class MessagePublic(BaseModel):
    """Schema for public message data in API responses."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
