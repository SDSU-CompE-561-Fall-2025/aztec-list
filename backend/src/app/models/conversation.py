"""
Conversation model.

This module defines the Conversation model for 1:1 messaging between users.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Uuid
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
    between the same two users through application-level checks.
    """

    __tablename__ = "conversations"

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

    # Relationships - eagerly load user data for username display
    user_1: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_1_id],
        lazy="joined",
    )
    user_2: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_2_id],
        lazy="joined",
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
