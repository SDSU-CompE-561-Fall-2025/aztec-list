from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AdminActionType

if TYPE_CHECKING:
    from app.models.user import User


class AdminAction(Base):
    """
    AdminAction model for moderation actions.

    Stores records of moderation actions (warnings, strikes, bans, listing removals)
    performed by admin users. Each action is linked to the admin who performed it
    and the user who received it.

    Audit Trail Integrity:
    - Admin actions are NEVER deleted when referenced entities are removed
    - Follows compliance best practices (preserve accountability/forensics)
    - Foreign keys use SET NULL to maintain historical records
    """

    __tablename__ = "admin_actions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    target_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"), index=True
    )
    action_type: Mapped[AdminActionType] = mapped_column(Enum(AdminActionType), index=True)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    # many-to-one → Each admin action is performed by one admin user
    # Admin user should never be deleted (business rule), but nullable for safety
    admin: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[admin_id],
        back_populates="admin_actions_performed",
    )

    # many-to-one → Each admin action targets one user (the subject)
    # Can be null if target user account is deleted (preserves audit trail)
    target_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="admin_actions_received",
    )
