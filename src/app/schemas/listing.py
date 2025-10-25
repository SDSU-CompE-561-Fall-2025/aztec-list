"""
Listing schemas.

This module contains Pydantic models for listing request/response validation.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl

from app.core.enums import Condition, ListingSortOrder


class ListingBase(BaseModel):
    """Base listing schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Short name of the item")
    description: str = Field(..., min_length=1, description="Detailed description of the item")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Price in USD, must be >= 0")
    category: str = Field(..., min_length=1, description="Category (e.g., electronics, books)")
    condition: Condition = Field(..., description="Item condition")


class ListingCreate(ListingBase):
    """Schema for creating a new listing."""


class ListingUpdate(BaseModel):
    """Schema for updating listing fields."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    price: Decimal | None = Field(None, ge=0, decimal_places=2)
    category: str | None = Field(None, min_length=1)
    condition: Condition | None = None
    is_active: bool | None = None


class ListingSearchParams(BaseModel):
    """Schema for listing search/filter parameters."""

    search_text: str | None = Field(None, description="Full-text search over title/description")
    category: str | None = Field(None, description="Filter by category")
    min_price: Decimal | None = Field(None, ge=0, description="Minimum price filter")
    max_price: Decimal | None = Field(None, ge=0, description="Maximum price filter")
    condition: Condition | None = Field(None, description="Filter by condition")
    seller_id: uuid.UUID | None = Field(None, description="Filter by seller UUID")
    limit: int = Field(20, ge=1, le=100, description="Page size (max 100)")
    offset: int = Field(0, ge=0, description="Number of records to skip")
    sort: ListingSortOrder = Field(ListingSortOrder.RECENT, description="Sort order")


class ListingSearchResponse(BaseModel):
    """Response schema for paginated listing search."""

    items: list["ListingPublic"] = Field(..., description="List of listings")
    next_cursor: str | None = Field(
        None, description="Cursor for next page (null for offset pagination)"
    )
    count: int = Field(..., description="Number of items in current response")

    model_config = {"from_attributes": True}


class UserListingsParams(BaseModel):
    """Schema for filtering user's listings."""

    limit: int = Field(20, ge=1, le=100, description="Page size (max 100)")
    offset: int = Field(0, ge=0, description="Number of records to skip")
    sort: ListingSortOrder = Field(ListingSortOrder.RECENT, description="Sort order")
    include_inactive: bool = Field(default=False, description="Include inactive listings")


class ListingPublic(ListingBase):
    """Schema for listing response."""

    id: uuid.UUID
    seller_id: uuid.UUID
    thumbnail_url: HttpUrl | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
