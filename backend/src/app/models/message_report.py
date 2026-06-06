"""
Message report model.

Stores user-submitted reports about direct messages. Unlike ``AdminAction``
(admin-initiated, single-state audit), a report is reactive and user-initiated and
carries a small status lifecycle (open -> dismissed / upheld). When a moderator
upholds a report, the resolution still emits a normal STRIKE ``AdminAction`` against
the message author, so the existing strike / auto-ban pipeline is reused.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import MessageReportCategory, MessageReportStatus

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class MessageReport(Base):
    """
    A user-submitted report about a single direct message.

    Foreign keys use SET NULL so deleting a message or a user never drops the report
    record (preserves the moderation audit trail). ``target_user_id`` is denormalized
    from the message's sender so the review queue can still show who was reported even
    after the underlying message is gone.
    """

    __tablename__ = "message_reports"
    __table_args__ = (
        # The admin queue lists OPEN reports newest-first; index the pair it filters on.
        Index("ix_message_reports_status_created_at", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    target_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), index=True
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    category: Mapped[MessageReportCategory] = mapped_column(Enum(MessageReportCategory), index=True)
    reason_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MessageReportStatus] = mapped_column(
        Enum(MessageReportStatus), default=MessageReportStatus.OPEN, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Denormalized copy of the offending message body, captured at report time. The
    # FK message may later be SET NULL (deletion), so this preserves what was reported.
    message_excerpt: Mapped[str | None] = mapped_column(String(500))

    # Relationships (all optional; SET NULL on delete). Disambiguated by foreign_keys
    # because three columns point at users.id.
    reporter: Mapped[User | None] = relationship("User", foreign_keys=[reporter_id])
    target_user: Mapped[User | None] = relationship("User", foreign_keys=[target_user_id])
    reviewed_by: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by_id])
    target_message: Mapped[Message | None] = relationship(
        "Message", foreign_keys=[target_message_id]
    )
