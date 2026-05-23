"""
MCP server exposing the marketplace as tools.

A small Model Context Protocol server (FastMCP) so an MCP client such as Claude
Desktop can browse Aztec List listings. The tools reuse the existing service layer,
so no business logic is duplicated here.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

from app.core.database import SessionLocal
from app.core.enums import Category
from app.schemas.listing import ListingPublic, ListingSearchParams, ListingSummary
from app.services.listing import listing_service

if TYPE_CHECKING:
    from app.models.listing import Listing

mcp = FastMCP("aztec-list")


def _summaries(listings: list[Listing]) -> list[dict]:
    return [ListingSummary.model_validate(listing).model_dump(mode="json") for listing in listings]


@mcp.tool()
def list_categories() -> list[str]:
    """List the available marketplace listing categories."""
    return [category.value for category in Category]


@mcp.tool()
def search_listings(  # noqa: PLR0913 - each parameter is part of the tool's schema
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Keyword search over active listings by exact text and structural filters.

    Matches only listings whose title or description literally contains the query
    text (substring match), plus optional category, price, and condition filters.
    Use this when the shopper gives concrete terms or filters (for example
    "desk under $50" or "electronics in good condition"). It will NOT match
    abbreviations, synonyms, or paraphrases (for example "GTA" will not find
    "Grand Theft Auto V"). For vague, abbreviated, or meaning-based queries, use
    semantic_search_listings instead.
    """
    params = ListingSearchParams(
        search_text=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        limit=limit,
    )
    db = SessionLocal()
    try:
        listings, _count = listing_service.get_filtered(db, params)
        return _summaries(listings)
    finally:
        db.close()


@mcp.tool()
def semantic_search_listings(query: str, limit: int = 10) -> list[dict]:
    """
    Meaning-based (semantic) search over active listings.

    Finds listings by meaning, so it matches abbreviations, synonyms, and
    paraphrases that keyword search misses (for example "GTA" finds "Grand Theft
    Auto V", and "something to listen to music" finds headphones). Prefer this for
    vague, natural-language, or abbreviated queries. It does not take category,
    price, or condition filters, so use search_listings when the shopper specifies
    those. Requires AI features to be enabled; if unavailable it falls back to
    keyword matching.
    """
    params = ListingSearchParams(search_text=query, semantic=True, limit=limit)
    db = SessionLocal()
    try:
        listings, _count = listing_service.get_filtered(db, params)
        return _summaries(listings)
    finally:
        db.close()


@mcp.tool()
def get_listing(listing_id: str) -> dict:
    """Get one listing with full details (including images) by its id."""
    db = SessionLocal()
    try:
        listing = listing_service.get_by_id(db, uuid.UUID(listing_id))
        return ListingPublic.model_validate(listing).model_dump(mode="json")
    finally:
        db.close()
