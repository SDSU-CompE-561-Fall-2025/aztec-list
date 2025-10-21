"""
Listing schemas.

This module contains Pydantic models for listing request/response validation.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl

from app.core.enums import Condition


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
    thumbnail_url: HttpUrl | None = None
    is_active: bool | None = None


class ListingPublic(ListingBase):
    """Schema for listing response."""

    id: uuid.UUID
    seller_id: uuid.UUID
    thumbnail_url: HttpUrl | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
