"""Integration tests for AI listing moderation (A1) and the review queue (E3)."""

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, Condition
from app.core.settings import settings
from app.models.listing import Listing
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.services.moderation import moderation_service

LISTINGS_URL = "/api/v1/listings"
FLAGGED_URL = "/api/v1/admin/flagged-listings"


class _FakeVerdictModel:
    """Stand-in for get_structured_model(...) returning a fixed moderation verdict."""

    def __init__(self, *, is_violation: bool, reason: str = "") -> None:
        self._verdict = SimpleNamespace(is_violation=is_violation, reason=reason)

    async def ainvoke(self, _messages: object) -> object:
        return self._verdict


class _BoomModel:
    """Stand-in whose ainvoke raises, to exercise the fail-open path."""

    async def ainvoke(self, _messages: object) -> object:
        raise RuntimeError("llm down")


class _HangingModel:
    """Stand-in whose ainvoke sleeps past the configured timeout."""

    def __init__(self, sleep_seconds: float = 5.0) -> None:
        self._sleep_seconds = sleep_seconds

    async def ainvoke(self, _messages: object) -> object:
        import asyncio

        await asyncio.sleep(self._sleep_seconds)
        return SimpleNamespace(is_violation=True, reason="should never see this")


def _enable_ai_review(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.moderation, "ai_review_enabled", True)


def _make_listing(db: Session, seller_id: uuid.UUID) -> Listing:
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title="Flagged thing",
        description="needs review",
        price=10.0,
        category="other",
        condition=Condition.GOOD,
        is_active=True,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


# --- A1: AI second-pass on listing creation -------------------------------------------------


@pytest.mark.integration
def test_borderline_listing_is_flagged_and_deactivated(
    authenticated_client: TestClient,
    db_session: Session,
    valid_listing_data: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_ai_review(monkeypatch)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_model",
        lambda _schema: _FakeVerdictModel(is_violation=True, reason="possible scam"),
    )

    response = authenticated_client.post(LISTINGS_URL, json=valid_listing_data)

    assert response.status_code == 201
    body = response.json()
    assert body["is_active"] is False
    actions = AdminActionRepository.get_by_target_listing_id(db_session, uuid.UUID(body["id"]))
    assert any(a.action_type == AdminActionType.FLAG for a in actions)


@pytest.mark.integration
def test_clean_listing_stays_active(
    authenticated_client: TestClient, valid_listing_data: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai_review(monkeypatch)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_model",
        lambda _schema: _FakeVerdictModel(is_violation=False),
    )

    response = authenticated_client.post(LISTINGS_URL, json=valid_listing_data)

    assert response.status_code == 201
    assert response.json()["is_active"] is True


@pytest.mark.integration
def test_review_disabled_skips_ai(
    authenticated_client: TestClient, valid_listing_data: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.moderation, "ai_review_enabled", False)
    # No model is mocked: if review ran it would hit a real provider. It must not run.
    response = authenticated_client.post(LISTINGS_URL, json=valid_listing_data)
    assert response.status_code == 201
    assert response.json()["is_active"] is True


@pytest.mark.integration
def test_ai_review_fails_open(
    authenticated_client: TestClient, valid_listing_data: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_ai_review(monkeypatch)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_model", lambda _schema: _BoomModel()
    )

    response = authenticated_client.post(LISTINGS_URL, json=valid_listing_data)

    assert response.status_code == 201
    assert response.json()["is_active"] is True


@pytest.mark.integration
def test_ai_review_timeout_fails_open(
    authenticated_client: TestClient, valid_listing_data: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A provider that hangs past the timeout must not block listing creation."""
    _enable_ai_review(monkeypatch)
    monkeypatch.setattr(settings.llm, "request_timeout_seconds", 0.05)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_model",
        lambda _schema: _HangingModel(sleep_seconds=2.0),
    )

    response = authenticated_client.post(LISTINGS_URL, json=valid_listing_data)

    assert response.status_code == 201
    # Fail-open: the slow provider must leave the listing active rather than blocking.
    assert response.json()["is_active"] is True


# --- E3: admin review queue -----------------------------------------------------------------


@pytest.mark.integration
def test_flagged_queue_lists_flagged_listing(
    admin_client: TestClient, db_session: Session, test_user: User
) -> None:
    listing = _make_listing(db_session, test_user.id)
    moderation_service._flag_listing(db_session, listing, "auto flag reason")  # noqa: SLF001

    response = admin_client.get(FLAGGED_URL)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    item = next(i for i in data["items"] if i["listing"]["id"] == str(listing.id))
    assert item["reason"] == "auto flag reason"


@pytest.mark.integration
def test_approve_flagged_listing_reactivates(
    admin_client: TestClient, db_session: Session, test_user: User
) -> None:
    listing = _make_listing(db_session, test_user.id)
    moderation_service._flag_listing(db_session, listing, "auto flag")  # noqa: SLF001
    assert listing.is_active is False

    response = admin_client.post(f"/api/v1/admin/listings/{listing.id}/approve")

    assert response.status_code == 200
    db_session.refresh(listing)
    assert listing.is_active is True
    remaining = AdminActionRepository.get_by_target_listing_id(db_session, listing.id)
    assert not [a for a in remaining if a.action_type == AdminActionType.FLAG]


@pytest.mark.integration
def test_flagged_queue_requires_admin(authenticated_client: TestClient) -> None:
    response = authenticated_client.get(FLAGGED_URL)
    assert response.status_code == 403
