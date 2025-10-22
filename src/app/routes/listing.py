import uuid
from typing import Annotated  # noqa: F401

from fastapi import APIRouter, Depends  # noqa: F401
from sqlalchemy.orm import Session  # noqa: F401

from app.core.database import get_db  # noqa: F401
from app.core.dependencies import get_current_user, get_current_user_id  # noqa: F401
from app.models.listing import Listing
from app.schemas.listing import (
    ListingCreate,  # noqa: F401
    ListingPublic,  # noqa: F401
    ListingSearchParams,  # noqa: F401
    ListingSearchResponse,  # noqa: F401
    ListingUpdate,  # noqa: F401
)
from app.services.listing import listing_service  # noqa: F401

listing_router = APIRouter(
    prefix="/listings",
    tag=["Listing"],
)


@listing_router.get("/")
async def get_listings() -> list["Listing"]:
    pass


@listing_router.post("/")
async def create_listing() -> Listing:
    pass


@listing_router.get("/{listing_id}")
async def get_listing_by_id(listing_id: uuid.UUID) -> Listing:
    pass


@listing_router.patch("/{listing_id}")
async def update_listing_by_id(listing_id: uuid.UUID) -> Listing:
    pass


@listing_router.delete("/{listing_id}")
async def delete_listing_by_id(listing_id: uuid.UUID) -> Listing:
    pass


@listing_router.get("{user_id}/")
async def get_user_listings(user_id: uuid.UUID) -> list["Listing"]:
    pass
