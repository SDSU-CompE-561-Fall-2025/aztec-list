"""
Conversation model.

This module defines the Conversation model for 1:1 messaging between users.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class Conversation(Base):
    """
    Conversation model for 1:1 messaging.

    Represents a conversation between two users. Each conversation has exactly
    two participants (user_1 and user_2). The system prevents duplicate conversations
    between the same two users through database-level unique constraint.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user_1_id", "user_2_id", name="uq_conversations_users"),
        CheckConstraint("user_1_id != user_2_id", name="ck_conversations_different_users"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_1_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    user_2_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    user_1: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_1_id],
        back_populates="conversations_as_user_1",
        lazy="select",
    )
    user_2: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_2_id],
        back_populates="conversations_as_user_2",
        lazy="select",
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
