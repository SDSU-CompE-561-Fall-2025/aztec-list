"""
User block routes.

Lets the authenticated user block / unblock another user and list everyone they
have blocked. Blocking is proactive and user-enforced (no admin involvement).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_verified_user
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.user_block import UserBlockListResponse, UserBlockPublic
from app.services.user_block import user_block_service

user_block_router = APIRouter(prefix="/users", tags=["User Blocks"])


@user_block_router.post(
    "/{user_id}/block",
    summary="Block a user",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute;50/hour")
async def block_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserBlockPublic:
    """
    Block another user (idempotent).

    The blocked user can no longer start a new conversation with, or send new
    messages to, the current user.

    Rate limit: 10 per minute (burst), 50 per hour (sustained).

    Raises:
        HTTPException: 400 on self-block, 404 if target missing, 403 if target is an admin.
    """
    block = user_block_service.block(db, current_user.id, user_id)
    return UserBlockPublic(
        blocked_user_id=block.blocked_id,
        blocked_username=None,
        created_at=block.created_at,
    )


@user_block_router.delete(
    "/{user_id}/block",
    summary="Unblock a user",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute;50/hour")
async def unblock_user(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Remove a block. Idempotent: unblocking a non-blocked user is a no-op."""
    user_block_service.unblock(db, current_user.id, user_id)


@user_block_router.get(
    "/me/blocks",
    summary="List users the current user has blocked",
)
async def list_my_blocks(
    current_user: Annotated[User, Depends(require_verified_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserBlockListResponse:
    """Return the accounts the current user has blocked, newest first."""
    items = user_block_service.list_blocks(db, current_user.id)
    return UserBlockListResponse(
        items=[UserBlockPublic(**item) for item in items],
        count=len(items),
    )
