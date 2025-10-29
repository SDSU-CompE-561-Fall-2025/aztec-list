import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.listing import Listing
from app.models.user import User
from app.schemas.listing import ListingPublic, UserListingsParams
from app.schemas.user import UserPublic
from app.services.listing import listing_service
from app.services.user import user_service

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get("/{user_id}", summary="Get a user's public profile", response_model=UserPublic)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get public user profile by ID.

    Args:
        user_id: The user's unique identifier (UUID)
        db: Database session

    Returns:
        UserPublic: Public user information

    Raises:
        HTTPException: 404 if user not found, 500 on database error
    """
    return user_service.get_by_id(db, user_id)


@user_router.get(
    "/{user_id}/listings", summary="Get user's listings", response_model=list[ListingPublic]
)
async def get_user_listings(
    db: Annotated[Session, Depends(get_db)],
    user_id: uuid.UUID,
    params: Annotated[UserListingsParams, Depends()],
) -> list[Listing]:
    return listing_service.get_by_seller(db, user_id, params)
