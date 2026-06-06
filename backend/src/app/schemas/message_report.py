"""
Message report schemas.

Pydantic models for the user-facing "report a message" flow and the admin
review queue that mirrors the flagged-listing pattern.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import MessageReportCategory, MessageReportStatus


class UserBasic(BaseModel):
    """Minimal user identity for moderation displays."""

    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class MessageReportCreate(BaseModel):
    """Schema for a user submitting a report about a message."""

    category: MessageReportCategory = Field(..., description="Why the message is being reported")
    reason_text: str | None = Field(
        None, max_length=1000, description="Optional free-text detail from the reporter"
    )


class MessageReportPublic(BaseModel):
    """The reporter's own view of a report they filed."""

    id: uuid.UUID
    category: MessageReportCategory
    reason_text: str | None = None
    status: MessageReportStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportedMessage(BaseModel):
    """The message a report points at (null if it was later deleted)."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageReportQueueItem(BaseModel):
    """A single report in the admin review queue."""

    report_id: uuid.UUID
    category: MessageReportCategory
    reason_text: str | None = None
    status: MessageReportStatus
    created_at: datetime
    reporter: UserBasic | None = None
    target_user: UserBasic | None = None
    # Live message if still present, else the excerpt captured at report time.
    message: ReportedMessage | None = None
    message_excerpt: str | None = None


class MessageReportQueueResponse(BaseModel):
    """Paginated list of message reports awaiting review."""

    items: list[MessageReportQueueItem]
    count: int


class MessageReportResolveRequest(BaseModel):
    """Optional admin override reason when upholding a report."""

    reason: str | None = Field(
        None, max_length=255, description="Override reason for the strike issued on uphold"
    )


class MessageReportUpheldResponse(BaseModel):
    """Outcome of upholding a report (strike may be skipped if the author is gone/banned)."""

    report_id: uuid.UUID
    status: MessageReportStatus
    strike_issued: bool = Field(
        ..., description="False if the author was already banned or their account is gone"
    )
    strike_count: int = Field(..., description="Author's total strikes after this action")
    auto_ban_triggered: bool = Field(
        default=False, description="True if this strike pushed the author to an automatic ban"
    )
