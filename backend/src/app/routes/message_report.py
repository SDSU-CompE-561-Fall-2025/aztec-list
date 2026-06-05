"""
Message report routes (user-facing).

Lets a conversation participant report another participant's message, and lets a
user see the reports they have filed. The admin review queue lives in
``routes/admin.py``.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_verified_user
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.message_report import (
    MessageReportCreate,
    MessageReportPublic,
)
from app.services.message_report import message_report_service

message_report_router = APIRouter(tags=["Message Reports"])


@message_report_router.post(
    "/messages/{message_id}/report",
    summary="Report a message for moderator review",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute;20/hour")
async def report_message(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    message_id: uuid.UUID,
    payload: MessageReportCreate,
    current_user: Annotated[User, Depends(require_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageReportPublic:
    """
    Report a message in one of the current user's conversations.

    Rate limit: 5 per minute (burst), 20 per hour (sustained).

    Raises:
        HTTPException: 404 if the message is gone, 403 if the user is not a
            participant, 400 if reporting their own message.
    """
    report = message_report_service.create(db, current_user, message_id, payload)
    return MessageReportPublic.model_validate(report)


@message_report_router.get(
    "/reports/me",
    summary="List reports the current user has filed",
)
async def list_my_reports(
    current_user: Annotated[User, Depends(require_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[MessageReportPublic]:
    """Return the current user's own report history, newest first."""
    reports = message_report_service.get_reports_for_reporter(db, current_user.id)
    return [MessageReportPublic.model_validate(r) for r in reports]
