from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserPublic
from app.services.user import user_service

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> UserPublic:
    """
    Get public user profile by ID.

    Args:
        user_id: The user's unique identifier
        db: Database session

    Returns:
        UserPublic: Public user information

    Raises:
        HTTPException: 404 if user not found, 500 on database error
    """
    return user_service.get_by_id(db, user_id)
