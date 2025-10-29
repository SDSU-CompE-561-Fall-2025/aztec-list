"""
Listing image model.

This module defines the Image model for listing images.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.listing import Listing


class Image(Base):
    """
    Image model for listing images.

    Represents an image associated with a listing. Each listing can have
    multiple images, with one designated as the thumbnail.
    """

    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String, unique=True)
    is_thumbnail: Mapped[bool] = mapped_column(Boolean, default=False)
    alt_text: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    listing: Mapped[Listing] = relationship(back_populates="images")
