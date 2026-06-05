"""
Message report service.

Business logic for user-submitted message reports and their admin resolution.

A report is created by a conversation participant against another participant's
message. Moderators review the queue and either dismiss the report or uphold it; an
uphold issues a STRIKE ``AdminAction`` against the message author, reusing the
existing strike / auto-ban pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.enums import MessageReportStatus
from app.repository.admin import AdminActionRepository
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository
from app.repository.message_report import MessageReportRepository
from app.schemas.admin import AdminActionStrike
from app.services.admin import admin_action_service

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.admin import AdminAction
    from app.models.message_report import MessageReport
    from app.models.user import User
    from app.schemas.message_report import MessageReportCreate

# Length of the message body snapshot stored on the report (matches the column width).
_EXCERPT_LEN = 500


class MessageReportService:
    """Service for message-report business logic."""

    def create(
        self,
        db: Session,
        reporter: User,
        target_message_id: uuid.UUID,
        payload: MessageReportCreate,
    ) -> MessageReport:
        """
        File a report against a message.

        Validates the message exists, the reporter is a participant of its
        conversation, and the reporter is not reporting their own message.

        Raises:
            HTTPException: 404 if the message is gone, 403 if the reporter is not a
                participant, 400 if reporting their own message.
        """
        message = MessageRepository.get_by_id(db, target_message_id)
        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        if message.sender_id == reporter.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot report your own message.",
            )

        if not ConversationRepository.is_participant(db, message.conversation_id, reporter.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only report messages in your own conversations.",
            )

        try:
            report = MessageReportRepository.create_no_commit(
                db,
                reporter_id=reporter.id,
                target_message_id=message.id,
                target_user_id=message.sender_id,
                category=payload.category,
                reason_text=payload.reason_text,
                message_excerpt=message.content[:_EXCERPT_LEN],
            )
            db.commit()
            db.refresh(report)
        except Exception:
            db.rollback()
            raise
        else:
            return report

    def get_reports_for_reporter(self, db: Session, reporter_id: uuid.UUID) -> list[MessageReport]:
        """All reports the given user has filed, newest first."""
        return MessageReportRepository.get_by_reporter(db, reporter_id)

    def list_queue(
        self,
        db: Session,
        report_status: MessageReportStatus = MessageReportStatus.OPEN,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Return the admin review queue for a given status, with its total count.

        Each item carries the report, the live message (or None if deleted), the
        captured excerpt, and the reporter / target usernames.
        """
        rows = MessageReportRepository.get_by_status(db, report_status, limit, offset)
        count = MessageReportRepository.count_by_status(db, report_status)
        items = [
            {
                "report_id": report.id,
                "category": report.category,
                "reason_text": report.reason_text,
                "status": report.status,
                "created_at": report.created_at,
                "reporter": (
                    {"id": report.reporter_id, "username": reporter_username}
                    if report.reporter_id
                    else None
                ),
                "target_user": (
                    {"id": report.target_user_id, "username": target_username}
                    if report.target_user_id
                    else None
                ),
                "message": message,
                "message_excerpt": report.message_excerpt,
            }
            for report, message, reporter_username, target_username in rows
        ]
        return items, count

    def _load_open_report(self, db: Session, report_id: uuid.UUID) -> MessageReport:
        """Fetch a report and assert it is still OPEN, else raise."""
        report = MessageReportRepository.get_by_id(db, report_id)
        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found",
            )
        if report.status != MessageReportStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This report has already been reviewed.",
            )
        return report

    def dismiss(self, db: Session, report_id: uuid.UUID, admin_id: uuid.UUID) -> MessageReport:
        """Resolve a report as DISMISSED (no action against the author)."""
        report = self._load_open_report(db, report_id)
        try:
            MessageReportRepository.mark_resolved(
                db, report, admin_id, MessageReportStatus.DISMISSED
            )
            db.commit()
            db.refresh(report)
        except Exception:
            db.rollback()
            raise
        else:
            return report

    def uphold(
        self,
        db: Session,
        report_id: uuid.UUID,
        admin_id: uuid.UUID,
        override_reason: str | None = None,
    ) -> tuple[MessageReport, AdminAction | None, int, bool]:
        """
        Resolve a report as UPHELD and strike the message author.

        Reuses ``admin_action_service.create_strike`` (which auto-bans at the configured
        threshold). If the author's account is gone or already banned, the report is
        still marked upheld but no new strike is issued.

        Returns:
            (report, strike_action_or_none, strike_count, auto_ban_triggered)

        Raises:
            HTTPException: 404 if missing, 409 if already reviewed, plus any error from
                the strike pipeline (e.g. 403 if the author is an admin).
        """
        report = self._load_open_report(db, report_id)
        author_id = report.target_user_id

        strike_action: AdminAction | None = None
        strike_count = 0
        auto_ban_triggered = False

        # Author deleted, or already banned: uphold without a duplicate penalty.
        author_gone = author_id is None
        already_banned = (
            author_id is not None
            and AdminActionRepository.has_active_ban(db, author_id) is not None
        )
        if not author_gone and not already_banned:
            reason = override_reason or f"Report upheld: {report.category.value}"
            strike_action, strike_count, auto_ban_triggered = admin_action_service.create_strike(
                db, admin_id, author_id, AdminActionStrike(reason=reason)
            )

        try:
            MessageReportRepository.mark_resolved(db, report, admin_id, MessageReportStatus.UPHELD)
            db.commit()
            db.refresh(report)
        except Exception:
            db.rollback()
            raise
        else:
            return report, strike_action, strike_count, auto_ban_triggered


# Service instance
message_report_service = MessageReportService()
