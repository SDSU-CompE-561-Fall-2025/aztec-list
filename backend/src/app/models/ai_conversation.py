"""
AI conversation models.

Stores the shopping-assistant chat history: one ``AIConversation`` per thread,
holding ordered ``AIMessage`` rows tagged USER or ASSISTANT. Assistant messages
may carry the listings they cited (``sources``).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AIMessageRole


class AIConversation(Base):
    """A shopping-assistant chat thread owned by one user."""

    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    messages: Mapped[list[AIMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at",
    )


class AIMessage(Base):
    """A single turn in an AI conversation (user prompt or assistant reply)."""

    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    ai_conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[AIMessageRole] = mapped_column(Enum(AIMessageRole))
    content: Mapped[str] = mapped_column(Text)
    # List of {"id": <listing uuid str>, "title": <str>} for cited listings (assistant only).
    sources: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    conversation: Mapped[AIConversation] = relationship(back_populates="messages")
