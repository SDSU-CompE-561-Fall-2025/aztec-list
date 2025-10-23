import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id  # noqa: F401
from app.models.listing import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingPublic,
    ListingSearchParams,  # noqa: F401
    ListingUpdate,
)
from app.services.listing import listing_service

listing_router = APIRouter(
    prefix="/listings",
    tags=["Listing"],
)


@listing_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_listing(
    db: Annotated[Session, Depends(get_db)],
    seller_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    listing: ListingCreate,
) -> ListingPublic:
    return listing_service.create(db, seller_id, listing)


@listing_router.get(
    "/{listing_id}",
    status_code=status.HTTP_200_OK,
)
async def get_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID
) -> ListingPublic:
    return listing_service.get_by_id(db, listing_id)


@listing_router.patch("/{listing_id}", status_code=status.HTTP_200_OK)
async def update_listing(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID, listing: ListingUpdate
) -> ListingPublic:
    return listing_service.update(db, listing_id, listing)


@listing_router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_to_delete: Listing
) -> None:
    return listing_service.delete(db, listing_to_delete)
