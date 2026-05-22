"""Integration tests for semantic listing search via the public API.

Validates the full wiring: the `semantic` query flag -> ListingService branch ->
vector store ranking -> get_by_ids ordering -> ListingSearchResponse. Uses an
in-memory Qdrant with a fake embedder (no model download).
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import Condition
from app.core.settings import settings
from app.models.listing import Listing
from app.models.user import User

LISTINGS_URL = "/api/v1/listings"


def _add_listing(db: Session, seller_id: uuid.UUID, title: str, description: str, category: str) -> Listing:
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title=title,
        description=description,
        price=40.0,
        category=category,
        condition=Condition.GOOD,
        is_active=True,
    )
    db.add(listing)
    db.commit()
    return listing


@pytest.mark.integration
def test_semantic_search_orders_by_relevance(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.vector, "score_floor", 0.0)
    monkeypatch.setattr(settings.vector, "relative_margin", 2.0)  # disable trimming for ordering check
    monkeypatch.setattr("app.services.listing.vector_store", memory_vector_store)

    desk = _add_listing(db_session, test_user.id, "Wooden study desk", "a sturdy desk", "furniture")
    _add_listing(db_session, test_user.id, "Office chair", "comfy seat", "furniture")
    _add_listing(db_session, test_user.id, "Gaming laptop", "fast machine", "electronics")

    memory_vector_store.ensure_collection()
    for listing in db_session.query(Listing).all():
        memory_vector_store.upsert_listing(listing)

    response = client.get(LISTINGS_URL, params={"search_text": "desk", "semantic": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3  # all active listings match the (empty) structural filter
    assert body["items"][0]["title"] == desk.title
    assert body["items"][0]["relevance_score"] is not None  # score surfaced for AI search


@pytest.mark.integration
def test_semantic_flag_ignored_when_ai_disabled(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    # AI off: the semantic flag is ignored and keyword (ILIKE) search is used.
    monkeypatch.setattr(settings.ai, "enabled", False)
    monkeypatch.setattr("app.services.listing.vector_store", memory_vector_store)

    _add_listing(db_session, test_user.id, "Vintage lamp", "a desk lamp", "furniture")

    response = client.get(LISTINGS_URL, params={"search_text": "desk", "semantic": "true"})

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    # keyword search matches the description "a desk lamp"
    assert "Vintage lamp" in titles


@pytest.mark.integration
def test_semantic_relative_cutoff_drops_weak_tail(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.vector, "score_floor", 0.0)
    monkeypatch.setattr(settings.vector, "relative_margin", 0.1)
    monkeypatch.setattr("app.services.listing.vector_store", memory_vector_store)

    _add_listing(db_session, test_user.id, "Wooden study desk", "a sturdy desk", "furniture")
    _add_listing(db_session, test_user.id, "Office chair", "comfy seat", "furniture")

    memory_vector_store.ensure_collection()
    for listing in db_session.query(Listing).all():
        memory_vector_store.upsert_listing(listing)

    response = client.get(LISTINGS_URL, params={"search_text": "desk", "semantic": "true"})

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    # the chair scores far below the desk and is trimmed by the relative cutoff
    assert titles == ["Wooden study desk"]


@pytest.mark.integration
def test_semantic_count_excludes_orphan_vectors(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    # A stale vector with no matching active DB row must not be counted or shown.
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.vector, "score_floor", 0.0)
    monkeypatch.setattr(settings.vector, "relative_margin", 2.0)
    monkeypatch.setattr("app.services.listing.vector_store", memory_vector_store)

    real = _add_listing(db_session, test_user.id, "Wooden desk", "a sturdy desk", "furniture")
    memory_vector_store.ensure_collection()
    memory_vector_store.upsert_listing(real)
    orphan = Listing(
        id=uuid.uuid4(),
        seller_id=test_user.id,
        title="Ghost desk",
        description="a desk",
        price=1,
        category="furniture",
        condition=Condition.GOOD,
        is_active=True,
    )
    memory_vector_store.upsert_listing(orphan)  # in the index, never in the DB

    response = client.get(LISTINGS_URL, params={"search_text": "desk", "semantic": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert [item["title"] for item in body["items"]] == ["Wooden desk"]
