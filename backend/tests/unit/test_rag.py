"""Unit tests for the RAG helpers (retrieval + prompt grounding)."""

import uuid

import pytest

from app.core.enums import Category, Condition
from app.core.settings import settings
from app.models.listing import Listing
from app.services import rag


def _listing(title: str, description: str = "", price: float = 10.0) -> Listing:
    return Listing(
        id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        title=title,
        description=description or title,
        price=price,
        category=Category.FURNITURE,
        condition=Condition.GOOD,
        is_active=True,
    )


@pytest.mark.unit
class TestRagHelpers:
    def test_format_context_empty(self) -> None:
        assert "no matching" in rag.format_context([]).lower()

    def test_format_context_includes_title_price_condition(self) -> None:
        ctx = rag.format_context([_listing("Wooden desk", "sturdy", price=40.0)])
        assert "Wooden desk" in ctx
        assert "$40.00" in ctx
        assert "good" in ctx

    def test_to_sources(self) -> None:
        listing = _listing("Desk")
        assert rag.to_sources([listing]) == [{"id": str(listing.id), "title": "Desk"}]

    def test_retrieve_listings_uses_vector_store(
        self, db_session, test_user, monkeypatch, memory_vector_store
    ) -> None:
        monkeypatch.setattr(settings.vector, "score_floor", 0.0)
        monkeypatch.setattr("app.services.rag.vector_store", memory_vector_store)
        desk = Listing(
            id=uuid.uuid4(),
            seller_id=test_user.id,
            title="Wooden desk",
            description="a sturdy desk",
            price=40.0,
            category="furniture",
            condition=Condition.GOOD,
            is_active=True,
        )
        db_session.add(desk)
        db_session.commit()
        memory_vector_store.ensure_collection()
        memory_vector_store.upsert_listing(desk)

        results = rag.retrieve_listings(db_session, "desk")

        assert [r.id for r in results] == [desk.id]
