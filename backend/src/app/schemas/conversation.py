"""
Conversation schemas.

This module contains Pydantic models for conversation request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    other_user_id: uuid.UUID = Field(..., description="UUID of the other user in the conversation")


class ConversationPublic(BaseModel):
    """Schema for public conversation data in API responses."""

    id: uuid.UUID
    user_1_id: uuid.UUID
    user_2_id: uuid.UUID
    user_1_username: str
    user_2_username: str
    created_at: datetime

    model_config = {"from_attributes": True}
