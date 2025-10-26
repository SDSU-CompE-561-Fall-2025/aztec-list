from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.listing import Listing


class Image(Base):
    """
    Image model for storing image metadata.

    Represents an image uploaded by a user, including its URL and upload timestamp.
    Has a many-to-one relationship with Profile.
    """

    __tablename__ = "listing_images"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), nullable=False)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    is_thumbnail: Mapped[bool] = mapped_column(default=False)
    alt_text: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # Relationships

    listing: Mapped[Listing] = relationship(back_populates="images")
