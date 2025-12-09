"""
Support ticket routes.

This module handles support ticket creation and management endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.dependencies import get_optional_user, require_admin
from app.core.email import email_service
from app.core.rate_limiter import limiter
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketStatusUpdate,
)

router = APIRouter(prefix="/support", tags=["support"])


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour;10/hour")
async def create_support_ticket(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    ticket_data: SupportTicketCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> SupportTicketResponse:
    """
    Create a new support ticket.

    Users can submit support tickets with or without being logged in.
    If logged in, the ticket will be associated with their account.
    Sends confirmation email to user and notification to support team.

    Rate limits:
    - All users: 3 tickets per hour (burst protection)
    - All users: 10 tickets per hour (hourly limit)

    Args:
        request: FastAPI request object (required for rate limiting)
        ticket_data: Support ticket data
        db: Database session
        current_user: Current authenticated user (optional)

    Returns:
        SupportTicket: Created support ticket

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    # Create ticket
    ticket = SupportTicket(
        user_id=current_user.id if current_user else None,
        email=ticket_data.email,
        subject=ticket_data.subject,
        message=ticket_data.message,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

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


@router.get("", response_model=list[SupportTicketResponse])
async def get_support_tickets(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
) -> list[SupportTicket]:
    """
    Get all support tickets (admin only).

    Args:
        db: Database session
        _: Admin user (required)
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


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SupportTicket:
    """
    Get a specific support ticket by ID (admin only).

    Args:
        ticket_id: ID of the ticket
        db: Database session
        _: Admin user (required)

    Returns:
        SupportTicket: Support ticket details

    Raises:
        HTTPException: If ticket not found
    """
    result = db.execute(
        select(SupportTicket)
        .options(selectinload(SupportTicket.user))
        .where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )

    return ticket


@router.patch("/{ticket_id}/status", response_model=SupportTicketResponse)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    status_update: SupportTicketStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SupportTicket:
    """
    Update support ticket status (admin only).

    Args:
        ticket_id: ID of the ticket
        status_update: New status data
        db: Database session
        _: Admin user (required)

    Returns:
        SupportTicket: Updated support ticket

    Raises:
        HTTPException: If ticket not found
    """
    result = db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found",
        )

    ticket.status = status_update.status
    db.commit()
    db.refresh(ticket)

    return ticket
