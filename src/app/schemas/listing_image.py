from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ImageBase(BaseModel):
    """Base schema for image data."""

    url: Annotated[str, HttpUrl]
    is_thumbnail: bool = False
    alt_text: str | None = None


class ImageCreate(ImageBase):
    """Schema for creating a new image."""

    listing_id: UUID


class ImageUpdate(BaseModel):
    """Schema for updating an image. All fields are optional."""

    url: Annotated[str, HttpUrl] | None = None
    is_thumbnail: bool | None = None
    alt_text: str | None = None


class ImagePublic(ImageBase):
    """Schema for image responses."""

    id: UUID
    listing_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
