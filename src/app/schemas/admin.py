"""
Admin action schemas.

This module contains Pydantic models for admin action request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ActionType


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


class AdminActionFilters(BaseModel):
    """Query parameters for filtering admin actions."""

    target_user_id: uuid.UUID | None = Field(None, description="Filter by target user ID")
    admin_id: uuid.UUID | None = Field(None, description="Filter by admin user ID")
    action_type: ActionType | None = Field(None, description="Filter by action type")
    target_listing_id: uuid.UUID | None = Field(None, description="Filter by listing ID")
    from_date: datetime | None = Field(
        None, alias="from", description="Filter actions created on or after this date"
    )
    to_date: datetime | None = Field(
        None, alias="to", description="Filter actions created on or before this date"
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    model_config = {"populate_by_name": True}
