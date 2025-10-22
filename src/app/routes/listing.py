import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_id  # noqa: F401
from app.models.listing import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingPublic,  # noqa: F401
    ListingSearchParams,  # noqa: F401
    ListingSearchResponse,  # noqa: F401
    ListingUpdate,
)
from app.services.listing import listing_service

listing_router = APIRouter(
    prefix="/listings",
    tag=["Listing"],
)


@listing_router.get("/")
async def get_listings() -> list["Listing"]:
    pass


@listing_router.get("{user_id}/")
async def get_user_listings(user_id: uuid.UUID) -> list["Listing"]:
    pass


@listing_router.get("/{listing_id}")
async def get_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID
) -> Listing:
    return listing_service.get_by_id(db, listing_id)


@listing_router.post("/")
async def create_listing(
    db: Annotated[Session, Depends(get_db)],
    seller_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    listing: ListingCreate,
) -> Listing:
    return listing_service.create(db, seller_id, listing)


@listing_router.patch("/{listing_id}")
async def update_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID, listing: ListingUpdate
) -> Listing:
    return listing_service.update(db, listing_id, listing)


@listing_router.delete("/{listing_id}")
async def delete_listing_by_id(
    db: Annotated[Session, Depends(get_db)], listing_id: uuid.UUID
) -> Listing:
    return listing_service.delete(db, listing_id)
