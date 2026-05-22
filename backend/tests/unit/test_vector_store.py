"""Unit tests for the Qdrant-backed vector store service.

These run against an in-memory Qdrant with a deterministic fake embedder, so they
are fast, offline, and do not download any model.
"""

import uuid

import pytest

from app.core.enums import Category, Condition
from app.models.listing import Listing
from app.services.vector_store import ListingFilter


def _listing(
    title: str,
    description: str = "",
    *,
    category: Category = Category.FURNITURE,
    condition: Condition = Condition.GOOD,
    price: float = 50.0,
    is_active: bool = True,
) -> Listing:
    """Build an in-memory Listing with the attributes upsert_listing reads."""
    return Listing(
        id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        title=title,
        description=description or title,
        price=price,
        category=category,
        condition=condition,
        is_active=is_active,
    )


@pytest.mark.unit
class TestVectorStore:
    """Vector store upsert/search/delete behavior."""

    def test_ensure_collection_is_idempotent(self, memory_vector_store) -> None:
        memory_vector_store.ensure_collection()
        memory_vector_store.ensure_collection()  # second call must not raise

    def test_upsert_and_search_ranks_by_similarity(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        desk = _listing("Wooden study desk", "a sturdy desk")
        chair = _listing("Office chair")
        laptop = _listing("Gaming laptop")
        for listing in (desk, chair, laptop):
            store.upsert_listing(listing)

        results = store.search("desk", limit=10)
        ids = [listing_id for listing_id, _score in results]

        assert ids[0] == desk.id
        assert set(ids) == {desk.id, chair.id, laptop.id}

    def test_search_filters_by_category(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        desk = _listing("Cheap desk", category=Category.FURNITURE)
        laptop = _listing("Cheap laptop", category=Category.ELECTRONICS)
        store.upsert_listing(desk)
        store.upsert_listing(laptop)

        results = store.search(
            "cheap", limit=10, listing_filter=ListingFilter(category=Category.ELECTRONICS)
        )
        ids = [listing_id for listing_id, _score in results]

        assert ids == [laptop.id]

    def test_inactive_listings_excluded_by_default(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        active = _listing("Active desk", is_active=True)
        inactive = _listing("Inactive desk", is_active=False)
        store.upsert_listing(active)
        store.upsert_listing(inactive)

        ids = [listing_id for listing_id, _score in store.search("desk", limit=10)]

        assert active.id in ids
        assert inactive.id not in ids

    def test_count_respects_filter(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        store.upsert_listing(_listing("Desk", category=Category.FURNITURE))
        store.upsert_listing(_listing("Laptop", category=Category.ELECTRONICS))

        assert store.count() == 2
        assert store.count(ListingFilter(category=Category.ELECTRONICS)) == 1

    def test_delete_removes_point(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        desk = _listing("Desk")
        store.upsert_listing(desk)
        assert store.count() == 1

        store.delete_listing(desk.id)

        assert store.count() == 0
        assert store.search("desk", limit=10) == []

    def test_score_threshold_drops_low_similarity(self, memory_vector_store) -> None:
        store = memory_vector_store
        store.ensure_collection()
        desk = _listing("Wooden study desk", "a sturdy desk")  # strong overlap with "desk"
        chair = _listing("Office chair")  # no overlap with "desk"
        store.upsert_listing(desk)
        store.upsert_listing(chair)

        results = store.search("desk", limit=10, score_threshold=0.8)
        ids = [listing_id for listing_id, _score in results]

        assert ids == [desk.id]
