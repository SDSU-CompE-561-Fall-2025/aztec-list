"""
Listing image schemas.

This module defines Pydantic schemas for listing image operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ImageBase(BaseModel):
    """Base schema for image data."""

    url: str = Field(..., description="URL path of the image (e.g., /uploads/images/uuid.jpg)")
    is_thumbnail: bool = Field(default=False, description="Whether this is the thumbnail image")
    alt_text: str | None = Field(None, description="Alternative text for the image")


class ImageCreate(ImageBase):
    """Schema for creating a new image."""


class ImageUpdate(BaseModel):
    """Schema for updating an existing image."""

    url: str | None = Field(None, description="URL path of the image")
    is_thumbnail: bool | None = Field(None, description="Whether this is the thumbnail image")
    alt_text: str | None = Field(None, description="Alternative text for the image")


class ImagePublic(ImageBase):
    """Schema for public image representation."""

    id: uuid.UUID = Field(..., description="Unique identifier for the image")
    listing_id: uuid.UUID = Field(..., description="ID of the listing this image belongs to")
    created_at: datetime = Field(..., description="Timestamp when the image was created")

    model_config = {"from_attributes": True}
