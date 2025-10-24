"""
Admin action schemas.

This module contains Pydantic models for admin action request/response validation.
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Enum for admin action types."""

    WARNING = "warning"
    STRIKE = "strike"
    BAN = "ban"
    LISTING_REMOVAL = "listing_removal"


class AdminActionBase(BaseModel):
    """Base admin action schema with common fields."""

    target_user_id: uuid.UUID = Field(..., description="User receiving the action")
    action_type: ActionType = Field(..., description="Type of moderation action")
    reason: str | None = Field(None, max_length=255, description="Brief explanation for audit log")
    target_listing_id: uuid.UUID | None = Field(
        None, description="Required if action_type is listing_removal"
    )
    expires_at: datetime | None = Field(
        None, description="End time for temporary ban (ISO 8601 datetime)"
    )


class AdminActionCreate(AdminActionBase):
    """Schema for creating a new admin action."""


class AdminActionPublic(BaseModel):
    """Schema for admin action response."""

    id: uuid.UUID
    admin_id: uuid.UUID
    target_user_id: uuid.UUID
    action_type: ActionType
    reason: str | None = None
    target_listing_id: uuid.UUID | None = None
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminActionWarning(BaseModel):
    """Schema for issuing a warning (convenience wrapper)."""

    reason: str | None = Field(None, max_length=255, description="Brief explanation for warning")


class AdminActionStrike(BaseModel):
    """Schema for adding a strike (convenience wrapper)."""

    reason: str | None = Field(None, max_length=255, description="Brief explanation for strike")


class AdminActionBan(BaseModel):
    """Schema for banning a user (convenience wrapper)."""

    reason: str | None = Field(None, max_length=255, description="Brief explanation for ban")
    expires_at: datetime | None = Field(
        None, description="End time for temporary ban; omit for permanent ban"
    )


class AdminListingRemoval(BaseModel):
    """Schema for removing a listing (convenience wrapper)."""

    reason: str | None = Field(None, max_length=255, description="Brief explanation for removal")


class AdminListingRestore(BaseModel):
    """Schema for restoring a listing."""

    reason: str | None = Field(
        None, max_length=255, description="Brief explanation for restoration"
    )


class AdminListingRemovalResponse(BaseModel):
    """Schema for listing removal response."""

    listing_id: uuid.UUID
    status: str
    admin_action: AdminActionPublic

    model_config = {"from_attributes": True}


class AdminListingRestoreResponse(BaseModel):
    """Schema for listing restore response."""

    listing_id: uuid.UUID
    status: str

    model_config = {"from_attributes": True}


class AdminActionListResponse(BaseModel):
    """Schema for paginated admin action list response."""

    items: list[AdminActionPublic]
    next_cursor: str | None = None
    count: int
