from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import Condition

if TYPE_CHECKING:
    from decimal import Decimal

    from app.models.user import User


class Listing(Base):
    """
    Listing model for marketplace items.

    Represents an item listed for sale by a user. Contains item details,
    pricing, condition, and status. Has relationships with User (seller),
    Images, and AdminActions.
    """

    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    category: Mapped[str] = mapped_column(String, index=True)
    condition: Mapped[Condition] = mapped_column(Enum(Condition))
    thumbnail_url: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    seller: Mapped[User] = relationship(back_populates="listings")
    # images: One-to-many with Image model (to be implemented)
    # admin_actions: One-to-many with AdminAction model (to be implemented)
