import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id  # noqa: F401
from app.schemas.listing import (
    ListingPublic,
    ListingSearchParams,  # noqa: F401
    ListingSearchResponse,  # noqa: F401
)
from app.services.listing import listing_service

listing_router = APIRouter(
    prefix="/listings",
    tags=["Listing"],
)


@listing_router.get(
    "/{listing_id}",
    status_code=status.HTTP_200_OK,
)
async def get_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID
) -> ListingPublic:
    return listing_service.get_by_id(db, listing_id)
