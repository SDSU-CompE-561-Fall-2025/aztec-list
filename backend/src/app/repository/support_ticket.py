"""
Support ticket repository.

This module provides data access layer for support ticket operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.support_ticket import SupportTicket

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.core.enums import TicketStatus
    from app.schemas.support_ticket import SupportTicketCreate


class SupportTicketRepository:
    """Repository for support ticket data access."""

    @staticmethod
    def get_by_id(db: Session, ticket_id: uuid.UUID) -> SupportTicket | None:
        """
        Get support ticket by ID.

        Args:
            db: Database session
            ticket_id: Ticket ID (UUID)

        Returns:
            SupportTicket | None: Support ticket if found, None otherwise
        """
        result = db.execute(
            select(SupportTicket)
            .options(selectinload(SupportTicket.user))
            .where(SupportTicket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[SupportTicket]:
        """
        Get all support tickets with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            list[SupportTicket]: List of support tickets
        """
        result = db.execute(
            select(SupportTicket)
            .options(selectinload(SupportTicket.user))
            .order_by(SupportTicket.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    def create(
        db: Session,
        ticket_data: SupportTicketCreate,
        user_id: uuid.UUID | None = None,
    ) -> SupportTicket:
        """
        Create a new support ticket.

        Args:
            db: Database session
            ticket_data: Support ticket creation data
            user_id: Optional user ID if authenticated

        Returns:
            SupportTicket: Created support ticket
        """
        ticket = SupportTicket(
            user_id=user_id,
            email=ticket_data.email,
            subject=ticket_data.subject,
            message=ticket_data.message,
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def update(db: Session, ticket: SupportTicket, new_status: TicketStatus) -> SupportTicket:
        """
        Update support ticket status.

        Args:
            db: Database session
            ticket: Support ticket to update
            new_status: New status value

        Returns:
            SupportTicket: Updated support ticket
        """
        ticket.status = new_status
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def delete(db: Session, ticket: SupportTicket) -> None:
        """
        Delete a support ticket.

        Args:
            db: Database session
            ticket: Support ticket to delete
        """
        db.delete(ticket)
        db.commit()
