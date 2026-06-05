"""
Message report repository.

Data access for the ``message_reports`` table: create a report, fetch one, list
by status for the admin queue (joined with messages + users, mirroring
``get_flagged_listings``), count, and mark resolved.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.models.message import Message
from app.models.message_report import MessageReport
from app.models.user import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.core.enums import MessageReportCategory, MessageReportStatus


class MessageReportRepository:
    """Repository for message-report data access."""

    @staticmethod
    def create_no_commit(  # noqa: PLR0913 - each field maps 1:1 to a column
        db: Session,
        reporter_id: uuid.UUID,
        target_message_id: uuid.UUID,
        target_user_id: uuid.UUID,
        category: MessageReportCategory,
        reason_text: str | None,
        message_excerpt: str | None,
    ) -> MessageReport:
        """Insert a report (caller commits)."""
        report = MessageReport(
            reporter_id=reporter_id,
            target_message_id=target_message_id,
            target_user_id=target_user_id,
            category=category,
            reason_text=reason_text,
            message_excerpt=message_excerpt,
        )
        db.add(report)
        db.flush()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_id(db: Session, report_id: uuid.UUID) -> MessageReport | None:
        """Fetch a single report by id."""
        return db.get(MessageReport, report_id)

    @staticmethod
    def get_by_reporter(db: Session, reporter_id: uuid.UUID) -> list[MessageReport]:
        """All reports a given user has filed, newest first."""
        query = (
            select(MessageReport)
            .where(MessageReport.reporter_id == reporter_id)
            .order_by(MessageReport.created_at.desc())
        )
        return list(db.scalars(query).all())

    @staticmethod
    def get_by_status(
        db: Session, report_status: MessageReportStatus, limit: int = 20, offset: int = 0
    ) -> list[tuple[MessageReport, Message | None, str | None, str | None]]:
        """
        Return (report, message, reporter_username, target_username) rows for a status.

        Outer-joins to messages (the message may have been SET NULL by deletion) and to
        the reporter / target users, newest first.
        """
        reporter = aliased(User, name="reporter")
        target = aliased(User, name="target")
        query = (
            select(MessageReport, Message, reporter.username, target.username)
            .outerjoin(Message, MessageReport.target_message_id == Message.id)
            .outerjoin(reporter, MessageReport.reporter_id == reporter.id)
            .outerjoin(target, MessageReport.target_user_id == target.id)
            .where(MessageReport.status == report_status)
            .order_by(MessageReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], row[1], row[2], row[3]) for row in db.execute(query).all()]

    @staticmethod
    def count_by_status(db: Session, report_status: MessageReportStatus) -> int:
        """Count reports in a given status."""
        query = select(func.count()).where(MessageReport.status == report_status)
        return db.scalar(query) or 0

    @staticmethod
    def mark_resolved(
        db: Session,
        report: MessageReport,
        admin_id: uuid.UUID,
        new_status: MessageReportStatus,
    ) -> MessageReport:
        """Stamp a report resolved (caller commits)."""
        report.status = new_status
        report.reviewed_by_id = admin_id
        report.reviewed_at = datetime.now(UTC)
        db.add(report)
        db.flush()
        return report
