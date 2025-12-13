"""
Test-only endpoints for E2E testing.

These endpoints are ONLY available when TEST__TEST_MODE environment variable is set to 'true'.
In production or when TEST__TEST_MODE is not set, these endpoints return 404.

Security Note:
- These endpoints bypass normal business logic for testing purposes
- Never deploy with TEST__TEST_MODE=true in production environments
- These are meant for automated E2E tests only
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.settings import settings
from app.models.user import User
from app.schemas.user import UserPublic
from app.services.user import user_service

test_router = APIRouter(
    prefix="/test",
    tags=["Test Helpers"],
)


def require_test_mode() -> None:
    """
    Dependency that ensures test endpoints are only accessible in test mode.

    Raises:
        HTTPException: 404 if not in test mode
    """
    if not settings.test.test_mode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )


@test_router.post(
    "/promote-to-admin/{user_id}",
    response_model=UserPublic,
    summary="[TEST ONLY] Promote user to admin role",
    dependencies=[Depends(require_test_mode)],
)
async def promote_user_to_admin(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Promote a user to admin role for testing purposes.

    This endpoint is ONLY available when TEST__TEST_MODE=true environment variable is set.
    It allows E2E tests to create admin users for testing admin functionality.

    Args:
        user_id: UUID of the user to promote
        db: Database session

    Returns:
        UserPublic: Updated user with admin role

    Raises:
        HTTPException: 404 if user not found or TEST__TEST_MODE is not enabled
    """
    user = user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user role to admin
    user.role = UserRole.ADMIN
    db.commit()
    db.refresh(user)

    return user
