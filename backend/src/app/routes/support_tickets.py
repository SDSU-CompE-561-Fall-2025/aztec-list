"""
Support ticket routes.

This module handles support ticket creation and management endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_optional_user, require_admin
from app.core.rate_limiter import limiter
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketStatusUpdate,
)
from app.services.support_ticket import support_ticket_service

router = APIRouter(prefix="/support", tags=["Support"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create support ticket",
    description="Submit a support ticket. Authentication optional - if logged in, ticket will be linked to your account.",
)
@limiter.limit("3/minute;10/hour")
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
    - All users: 3 tickets per minute (burst protection)
    - All users: 10 tickets per hour (sustained limit)

    Args:
        request: FastAPI request object (required for rate limiting)
        ticket_data: Support ticket data
        db: Database session
        current_user: Current authenticated user (optional)

    Returns:
        SupportTicketResponse: Created support ticket with email status

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    return support_ticket_service.create(db, ticket_data, current_user)


@router.get(
    "",
    response_model=list[SupportTicketResponse],
    summary="List all support tickets",
    description="Retrieve all support tickets with pagination. Admin access required.",
)
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
        list[SupportTicketResponse]: List of support tickets
    """
    return support_ticket_service.get_all(db, skip=skip, limit=limit)


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
    summary="Get support ticket by ID",
    description="Retrieve a specific support ticket by its ID. Admin access required.",
)
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
        SupportTicketResponse: Support ticket details

    Raises:
        HTTPException: If ticket not found
    """
    return support_ticket_service.get_by_id(db, ticket_id)


@router.patch(
    "/{ticket_id}/status",
    response_model=SupportTicketResponse,
    summary="Update ticket status",
    description="Update the status of a support ticket (OPEN, IN_PROGRESS, RESOLVED, CLOSED). Admin access required.",
)
@limiter.limit("10/minute;50/hour")
async def update_ticket_status(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    ticket_id: uuid.UUID,
    status_update: SupportTicketStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SupportTicket:
    """
    Update support ticket status (admin only).

    Rate limit: 10 per minute (burst), 50 per hour (sustained) - generous for admin operations.

    Args:
        request: FastAPI request object (required for rate limiting)
        ticket_id: ID of the ticket
        status_update: New status data
        db: Database session
        _: Admin user (required)

    Returns:
        SupportTicketResponse: Updated support ticket

    Raises:
        HTTPException: If ticket not found
    """
    return support_ticket_service.update_status(db, ticket_id, status_update.status)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete support ticket",
    description="Permanently delete a support ticket. Useful for removing spam or test tickets. Admin access required.",
)
@limiter.limit("5/minute;20/hour")
async def delete_support_ticket(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    ticket_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Delete a support ticket (admin only).

    Rate limit: 5 per minute (burst), 20 per hour (sustained) - moderate for admin operations.

    Useful for removing test tickets or spam.

    Args:
        request: FastAPI request object (required for rate limiting)
        ticket_id: ID of the ticket to delete
        db: Database session
        _: Admin user (required)

    Raises:
        HTTPException: If ticket not found
    """
    support_ticket_service.delete(db, ticket_id)
