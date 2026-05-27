"""Integration tests for AI image moderation (A2)."""

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, Condition
from app.core.settings import settings
from app.models.listing import Listing
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.services.moderation import moderation_service


class _FakeVision:
    """Stand-in for get_structured_vision_model(...) returning a fixed verdict."""

    def __init__(self, *, is_violation: bool, reason: str = "") -> None:
        self._verdict = SimpleNamespace(is_violation=is_violation, reason=reason)

    async def ainvoke(self, _messages: object) -> object:
        return self._verdict


class _BoomVision:
    """Stand-in whose ainvoke raises, to exercise the fail-open path."""

    async def ainvoke(self, _messages: object) -> object:
        raise RuntimeError("vision down")


def _make_listing(db: Session, seller_id: uuid.UUID) -> Listing:
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title="Item with photo",
        description="see image",
        price=20.0,
        category="other",
        condition=Condition.GOOD,
        is_active=True,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def _write_image(tmp_path: Path, listing_id: uuid.UUID) -> str:
    listing_dir = tmp_path / str(listing_id)
    listing_dir.mkdir(parents=True, exist_ok=True)
    (listing_dir / "photo.jpg").write_bytes(b"fake-image-bytes")
    return f"/uploads/images/{listing_id}/photo.jpg"


def _enable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.moderation, "ai_image_review_enabled", True)
    monkeypatch.setattr(settings.storage, "upload_dir", str(tmp_path))


def _has_flag(db: Session, listing_id: uuid.UUID) -> bool:
    actions = AdminActionRepository.get_by_target_listing_id(db, listing_id)
    return any(a.action_type == AdminActionType.FLAG for a in actions)


@pytest.mark.integration
async def test_violation_flags_listing(
    db_session: Session, test_user: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _enable(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_vision_model",
        lambda _schema: _FakeVision(is_violation=True, reason="nudity"),
    )
    listing = _make_listing(db_session, test_user.id)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_user, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is False
    assert _has_flag(db_session, listing.id)


@pytest.mark.integration
async def test_clean_image_keeps_active(
    db_session: Session, test_user: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _enable(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_vision_model",
        lambda _schema: _FakeVision(is_violation=False),
    )
    listing = _make_listing(db_session, test_user.id)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_user, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is True
    assert not _has_flag(db_session, listing.id)


@pytest.mark.integration
async def test_disabled_is_noop(
    db_session: Session, test_user: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(settings.ai, "enabled", True)
    monkeypatch.setattr(settings.moderation, "ai_image_review_enabled", False)
    monkeypatch.setattr(settings.storage, "upload_dir", str(tmp_path))
    listing = _make_listing(db_session, test_user.id)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_user, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is True


@pytest.mark.integration
async def test_vision_failure_fails_open(
    db_session: Session, test_user: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _enable(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_vision_model", lambda _schema: _BoomVision()
    )
    listing = _make_listing(db_session, test_user.id)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_user, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is True


@pytest.mark.integration
async def test_image_over_size_limit_is_skipped(
    db_session: Session, test_user: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Images larger than the vision provider's byte cap should skip moderation entirely."""
    _enable(monkeypatch, tmp_path)
    # Force the byte cap below the test image's size so the guard short-circuits.
    monkeypatch.setattr("app.services.moderation._MAX_VISION_BYTES", 16)

    called = False

    class _ShouldNotRun:
        async def ainvoke(self, _messages: object) -> object:
            nonlocal called
            called = True
            return SimpleNamespace(is_violation=True, reason="should not be called")

    monkeypatch.setattr(
        "app.services.moderation.get_structured_vision_model", lambda _schema: _ShouldNotRun()
    )
    listing = _make_listing(db_session, test_user.id)
    # `_write_image` writes 16 bytes ("fake-image-bytes"); the guard checks `>`, so we
    # need it strictly larger than the cap.
    monkeypatch.setattr("app.services.moderation._MAX_VISION_BYTES", 8)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_user, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is True
    assert called is False, "vision provider should not be called when image exceeds size limit"


@pytest.mark.integration
async def test_admin_upload_bypasses(
    db_session: Session, test_admin: User, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _enable(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.services.moderation.get_structured_vision_model",
        lambda _schema: _FakeVision(is_violation=True, reason="x"),
    )
    listing = _make_listing(db_session, test_admin.id)
    url = _write_image(tmp_path, listing.id)

    await moderation_service.review_listing_image(db_session, test_admin, listing, url)

    db_session.refresh(listing)
    assert listing.is_active is True
