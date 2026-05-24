"""Integration tests for similar-listings discovery (C1)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import Condition
from app.core.settings import settings
from app.models.listing import Listing
from app.models.user import User


def _add_indexed_listing(
    db: Session,
    seller_id: uuid.UUID,
    store,
    title: str,
    description: str,
    *,
    is_active: bool = True,
) -> Listing:
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title=title,
        description=description,
        price=40.0,
        category="furniture",
        condition=Condition.GOOD,
        is_active=is_active,
    )
    db.add(listing)
    db.commit()
    store.ensure_collection()
    store.upsert_listing(listing)
    return listing


@pytest.mark.integration
def test_similar_listings_ranks_neighbours_and_excludes_self(
    client: TestClient,
    db_session: Session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
    memory_vector_store,
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.vector, "score_floor", 0.0)
    monkeypatch.setattr("app.services.listing.vector_store", memory_vector_store)

    desk = _add_indexed_listing(
        db_session, test_user.id, memory_vector_store, "Wooden study desk", "a sturdy desk for a dorm"
    )
    desk2 = _add_indexed_listing(
        db_session, test_user.id, memory_vector_store, "Standing desk", "an adjustable desk"
    )
    _add_indexed_listing(
        db_session, test_user.id, memory_vector_store, "Mountain bike", "a fast bike"
    )

    response = client.get(f"/api/v1/listings/{desk.id}/similar")

    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert str(desk.id) not in ids  # self excluded
    assert ids[0] == str(desk2.id)  # closest neighbour ranked first


@pytest.mark.integration
def test_similar_listings_disabled_returns_empty(
    client: TestClient, test_listing: Listing, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", False)
    response = client.get(f"/api/v1/listings/{test_listing.id}/similar")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.integration
def test_similar_listings_unknown_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/listings/{uuid.uuid4()}/similar")
    assert response.status_code == 404
