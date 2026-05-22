"""
Backfill script: embed all existing listings into the vector store.

Run from the backend/ directory after enabling AI features (AI__ENABLED=true):

    uv run python scripts/reindex_listings.py

Uses the configured database and vector store - an embedded on-disk Qdrant by
default, or a remote server when VECTOR__QDRANT_URL is set. This is a full
rebuild: the collection is dropped and recreated, clearing any orphan vectors
left behind by deletes/deactivations that happened while AI was disabled.
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

# Make the `app` package importable when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.listing import Listing
from app.services.vector_store import vector_store

# Side effect: load every ORM model so SQLAlchemy can resolve relationship()
# targets (e.g. Listing.seller -> User) before querying. Done via import_module
# (not a bare import) so it doesn't read as an unused import.
importlib.import_module("app.api.v1.routes")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reindex_listings")


def main() -> None:
    """Drop the collection and re-embed every listing (clean rebuild)."""
    vector_store.reset_collection()
    db = SessionLocal()
    try:
        listings = list(db.scalars(select(Listing)))
        for listing in listings:
            vector_store.upsert_listing(listing)
        logger.info("Indexed %d listings", len(listings))
    finally:
        db.close()
        vector_store.close()


if __name__ == "__main__":
    main()
