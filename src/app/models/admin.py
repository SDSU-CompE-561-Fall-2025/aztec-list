from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.admin import Admin
    from app.models.user import User

AdminActionType = Enum(
    "warning",
    "strike",
    "ban",
    "listing_removal",
    name="admin_action_type",
)


class Admin(Base):
    """
    Admin model for moderation actions.

    The admin will have the ability to block individuals,
    and give a short reason why.
    """

    __tablename__ = "admin"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[str] = mapped_column(AdminActionType, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    admin: Mapped[User] = relationship(
        "User",
        foreign_keys=[admin_id],
        back_populates="admin_actions_performed",
    )

    # many-to-one → Each admin action targets one user (the subject).
    target_user: Mapped[User] = relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="admin_actions_received",
    )
