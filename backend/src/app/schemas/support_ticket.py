"""
Schemas for support ticket operations.

This module defines Pydantic models for validating and serializing
support ticket data in API requests and responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import TicketStatus


class SupportTicketCreate(BaseModel):
    """Schema for creating a support ticket."""

    email: EmailStr = Field(..., max_length=254, description="Email address for contact")
    subject: str = Field(..., min_length=3, max_length=200, description="Ticket subject")
    message: str = Field(..., min_length=10, max_length=2000, description="Ticket message")


class SupportTicketResponse(BaseModel):
    """Schema for support ticket in responses."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    email: str
    subject: str
    message: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    email_sent: bool = Field(
        default=True, description="Whether confirmation email was sent successfully"
    )

    class Config:
        from_attributes = True


class SupportTicketStatusUpdate(BaseModel):
    """Schema for updating ticket status."""

    status: TicketStatus = Field(..., description="New status for the ticket")
