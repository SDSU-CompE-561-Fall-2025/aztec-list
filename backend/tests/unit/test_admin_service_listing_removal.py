"""
Unit tests for AdminActionService remove_listing_with_strike.

Tests for the complex business logic of listing removal with automatic strikes and bans.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, UserRole
from app.models.admin import AdminAction
from app.models.listing import Listing
from app.models.user import User
from app.schemas.admin import AdminActionCreate
from app.services.admin import AdminActionService


@pytest.fixture
def admin_service() -> AdminActionService:
    """Create AdminActionService instance for testing."""
    return AdminActionService()


@pytest.fixture
def mock_admin() -> User:
    """Create a mock admin user."""
    return User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@example.edu",
        hashed_password="hashed",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_user() -> User:
    """Create a mock regular user."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.edu",
        hashed_password="hashed",
        role=UserRole.USER,
    )


@pytest.fixture
def mock_listing(mock_user: User) -> Listing:
    """Create a mock listing."""
    return Listing(
        id=uuid.uuid4(),
        seller_id=mock_user.id,
        title="Test Listing",
        description="Test description",
        price=100.0,
    )


class TestRemoveListingWithStrike:
    """Test AdminActionService remove_listing_with_strike method."""

    @patch("app.services.admin.settings")
    def test_remove_listing_issues_strike_and_creates_removal_record(
        self,
        mock_settings,
        admin_service: AdminActionService,
        mock_admin: User,
        mock_listing: Listing,
        mock_user: User,
    ):
        """Test removing listing issues strike and creates LISTING_REMOVAL record."""
        mock_settings.moderation.strike_auto_ban_threshold = 3

        removal_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_listing.seller_id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test violation",
            target_listing_id=mock_listing.id,
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.count_strikes") as mock_count,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.return_value = mock_user
            mock_has_ban.return_value = None  # Not banned
            mock_count.return_value = 1  # One strike after this action
            mock_create.return_value = removal_action
            db = MagicMock(spec=Session)

            result = admin_service.remove_listing_with_strike(
                db, mock_admin.id, mock_listing.id, "Test violation"
            )

            assert result == removal_action
            mock_delete.assert_called_once_with(db, mock_listing)
            # Should create removal action + strike
            assert mock_create.call_count == 2
            db.commit.assert_called_once()

    @patch("app.services.admin.settings")
    def test_remove_listing_triggers_auto_ban_at_threshold(
        self,
        mock_settings,
        admin_service: AdminActionService,
        mock_admin: User,
        mock_listing: Listing,
        mock_user: User,
    ):
        """Test removing listing triggers auto-ban when strike threshold is reached."""
        mock_settings.moderation.strike_auto_ban_threshold = 3

        removal_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_listing.seller_id,
            action_type=AdminActionType.LISTING_REMOVAL,
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.count_strikes") as mock_count,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.return_value = mock_user
            mock_has_ban.return_value = None  # Not banned
            mock_count.return_value = 3  # Reaches threshold
            mock_create.return_value = removal_action
            db = MagicMock(spec=Session)

            admin_service.remove_listing_with_strike(
                db, mock_admin.id, mock_listing.id, "Test violation"
            )

            # Should create removal action + strike + ban
            assert mock_create.call_count == 3

            # Verify ban action was created with correct details
            calls = mock_create.call_args_list
            ban_call = calls[2]  # Third call should be the ban
            ban_data = ban_call[0][2]  # AdminActionCreate object
            assert ban_data.action_type == AdminActionType.BAN
            assert "3 strikes" in ban_data.reason

    def test_remove_listing_skips_strike_if_already_banned(
        self,
        admin_service: AdminActionService,
        mock_admin: User,
        mock_listing: Listing,
        mock_user: User,
    ):
        """Test removing listing skips issuing strike if user is already banned."""
        existing_ban = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
        )

        removal_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_listing.seller_id,
            action_type=AdminActionType.LISTING_REMOVAL,
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.return_value = mock_user
            mock_has_ban.return_value = existing_ban  # Already banned
            mock_create.return_value = removal_action
            db = MagicMock(spec=Session)

            admin_service.remove_listing_with_strike(
                db, mock_admin.id, mock_listing.id, "Test violation"
            )

            # Should only create removal action, not strike or ban
            assert mock_create.call_count == 1
            mock_delete.assert_called_once()

    def test_remove_listing_not_found_raises_404(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test removing non-existent listing raises 404."""
        fake_listing_id = uuid.uuid4()

        with patch("app.services.admin.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service.remove_listing_with_strike(db, mock_admin.id, fake_listing_id, "Test")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(fake_listing_id) in exc_info.value.detail

    def test_remove_listing_owned_by_admin_raises_403(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test removing listing owned by admin raises 403."""
        admin_listing = Listing(
            id=uuid.uuid4(),
            seller_id=mock_admin.id,
            title="Admin Listing",
            description="Test",
            price=100.0,
        )

        admin_as_seller = User(
            id=mock_admin.id,
            username="admin",
            email="admin@example.edu",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
        ):
            mock_get_listing.return_value = admin_listing
            mock_get_user.return_value = admin_as_seller
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service.remove_listing_with_strike(
                    db, mock_admin.id, admin_listing.id, "Test"
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "admin" in exc_info.value.detail.lower()

    def test_remove_listing_rollback_on_exception(
        self,
        admin_service: AdminActionService,
        mock_admin: User,
        mock_listing: Listing,
        mock_user: User,
    ):
        """Test that transaction is rolled back if an exception occurs."""
        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.return_value = mock_user
            mock_create.side_effect = Exception("Database error")
            db = MagicMock(spec=Session)

            with pytest.raises(Exception) as exc_info:
                admin_service.remove_listing_with_strike(db, mock_admin.id, mock_listing.id, "Test")

            assert "Database error" in str(exc_info.value)
            db.rollback.assert_called_once()
