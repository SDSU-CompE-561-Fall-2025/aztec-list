"""
User block model.

Records that one user has blocked another. A block is proactive and
user-enforced (no admin involvement): the blocked party can no longer start a new
conversation with, or deliver new messages to, the blocker. Enforcement is
one-directional and asymmetric - ``blocker`` blocking ``blocked`` does not stop the
blocker from messaging the blocked user.
"""

from __future__ import annotations

import uuid  # noqa: TC003 - SQLAlchemy resolves Mapped[uuid.UUID] at runtime
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserBlock(Base):
    """
    A single directional block: ``blocker_id`` has blocked ``blocked_id``.

    Composite primary key on (blocker_id, blocked_id) makes a block idempotent and
    gives a fast membership lookup. Both FKs CASCADE so blocks vanish when either
    account is deleted (no audit value in retaining a block once a user is gone).
    """

    __tablename__ = "user_blocks"
    __table_args__ = (
        CheckConstraint("blocker_id != blocked_id", name="ck_user_blocks_different_users"),
    )

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    blocker: Mapped[User] = relationship("User", foreign_keys=[blocker_id])
    blocked: Mapped[User] = relationship("User", foreign_keys=[blocked_id])
