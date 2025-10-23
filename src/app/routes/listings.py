from fastapi import APIRouter

from app.core.dependencies import get_current_user, get_current_user_id  # noqa: F401
from app.schemas.listing import (
    ListingSearchParams,  # noqa: F401
    ListingSearchResponse,  # noqa: F401
)

listing_router = APIRouter(
    prefix="/listings",
    tags=["Listing"],
)
