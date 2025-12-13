"""
Support ticket service.

This module contains business logic for support ticket operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.core.email import email_service
from app.repository.support_ticket import SupportTicketRepository
from app.schemas.support_ticket import SupportTicketResponse

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.core.enums import TicketStatus
    from app.models.support_ticket import SupportTicket
    from app.models.user import User
    from app.schemas.support_ticket import SupportTicketCreate


class SupportTicketService:
    """Service for support ticket business logic."""

    def get_by_id(self, db: Session, ticket_id: uuid.UUID) -> SupportTicket:
        """
        Get support ticket by ID.

        Args:
            db: Database session
            ticket_id: Ticket ID

        Returns:
            SupportTicket: Support ticket object

        Raises:
            HTTPException: If ticket not found
        """
        ticket = SupportTicketRepository.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )
        return ticket

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[SupportTicket]:
        """
        Get all support tickets with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            list[SupportTicket]: List of support tickets
        """
        return SupportTicketRepository.get_all(db, skip=skip, limit=limit)

    def create(
        self,
        db: Session,
        ticket_data: SupportTicketCreate,
        current_user: User | None = None,
    ) -> SupportTicketResponse:
        """
        Create a new support ticket and send notification emails.

        Args:
            db: Database session
            ticket_data: Support ticket creation data
            current_user: Current authenticated user (optional)

        Returns:
            SupportTicketResponse: Created support ticket with email status
        """
        # Create ticket via repository
        user_id = current_user.id if current_user else None
        ticket = SupportTicketRepository.create(db, ticket_data, user_id)

        # Send confirmation email to user
        confirmation_sent = email_service.send_support_ticket_confirmation(
            email=ticket.email,
            subject=ticket.subject,
            ticket_id=str(ticket.id),
        )

        # Send notification to support team
        notification_sent = email_service.send_support_ticket_notification(
            email=ticket.email,
            username=current_user.username if current_user else None,
            subject=ticket.subject,
            message=ticket.message,
            ticket_id=str(ticket.id),
        )

        # Return ticket with email status
        response_data = SupportTicketResponse.model_validate(ticket)
        response_data.email_sent = confirmation_sent and notification_sent
        return response_data

    def update_status(
        self, db: Session, ticket_id: uuid.UUID, new_status: TicketStatus
    ) -> SupportTicket:
        """
        Update support ticket status.

        Args:
            db: Database session
            ticket_id: Ticket ID
            new_status: New status value

        Returns:
            SupportTicket: Updated support ticket

        Raises:
            HTTPException: If ticket not found
        """
        # Get the actual ticket model from repository
        ticket = SupportTicketRepository.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )
        return SupportTicketRepository.update(db, ticket, new_status)

    def delete(self, db: Session, ticket_id: uuid.UUID) -> None:
        """
        Delete a support ticket.

        Args:
            db: Database session
            ticket_id: Ticket ID

        Raises:
            HTTPException: If ticket not found
        """
        ticket = SupportTicketRepository.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support ticket not found",
            )
        SupportTicketRepository.delete(db, ticket)


# Global service instance
support_ticket_service = SupportTicketService()
