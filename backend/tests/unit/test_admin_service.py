"""
Unit tests for AdminActionService.

Tests the business logic layer for admin action operations.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, UserRole
from app.models.admin import AdminAction
from app.models.listing import Listing
from app.models.user import User
from app.schemas.admin import (
    AdminActionBan,
    AdminActionCreate,
    AdminActionFilters,
    AdminActionStrike,
)
from app.services.admin import AdminActionService


@pytest.fixture
def admin_service():
    """Create AdminActionService instance."""
    return AdminActionService()


@pytest.fixture
def mock_admin():
    """Create a mock admin user."""
    return User(
        id=uuid.uuid4(),
        username="adminuser",
        email="admin@example.com",
        hashed_password="hashed",
        is_verified=True,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_user():
    """Create a mock regular user."""
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_verified=True,
        role=UserRole.USER,
    )


@pytest.fixture
def mock_action():
    """Create a mock admin action."""
    return AdminAction(
        id=uuid.uuid4(),
        admin_id=uuid.uuid4(),
        target_user_id=uuid.uuid4(),
        action_type=AdminActionType.STRIKE,
        reason="Test violation",
        created_at=datetime.now(UTC),
    )


class TestAdminServiceValidation:
    """Test AdminActionService validation methods."""

    def test_validate_moderation_participants_success(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test successful validation of moderation participants."""
        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get,
            patch("app.services.admin.ensure_can_moderate_user") as mock_ensure,
        ):
            mock_get.side_effect = [mock_user, mock_admin]
            db = MagicMock(spec=Session)

            target, admin = admin_service._validate_moderation_participants(
                db, mock_admin.id, mock_user.id
            )

            assert target == mock_user
            assert admin == mock_admin
            mock_ensure.assert_called_once_with(mock_user, mock_admin)

    def test_validate_moderation_participants_target_not_found(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test validation when target user not found."""
        with patch("app.services.admin.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            target_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service._validate_moderation_participants(db, mock_admin.id, target_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(target_id) in exc_info.value.detail

    def test_validate_moderation_participants_admin_not_found(
        self, admin_service: AdminActionService, mock_user: User
    ):
        """Test validation when admin user not found."""
        with patch("app.services.admin.UserRepository.get_by_id") as mock_get:
            mock_get.side_effect = [mock_user, None]  # Target found, admin not found
            db = MagicMock(spec=Session)
            admin_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service._validate_moderation_participants(db, admin_id, mock_user.id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(admin_id) in exc_info.value.detail

    def test_validate_moderation_participants_cannot_moderate_admin(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test that admins cannot moderate other admins."""
        another_admin = User(
            id=uuid.uuid4(),
            username="anotheradmin",
            email="admin2@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get,
            patch("app.services.admin.ensure_can_moderate_user") as mock_ensure,
        ):
            mock_get.side_effect = [another_admin, mock_admin]
            mock_ensure.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot moderate admin users"
            )
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service._validate_moderation_participants(db, mock_admin.id, another_admin.id)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_check_user_not_banned_passes_when_not_banned(
        self, admin_service: AdminActionService, mock_user: User
    ):
        """Test check passes when user is not banned."""
        strike_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=uuid.uuid4(),
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Strike",
        )

        with patch("app.services.admin.AdminActionRepository.get_by_target_user_id") as mock_get:
            mock_get.return_value = [strike_action]
            db = MagicMock(spec=Session)

            # Should not raise
            admin_service._check_user_not_banned(db, mock_user.id)

    def test_check_user_not_banned_raises_when_banned(
        self, admin_service: AdminActionService, mock_user: User
    ):
        """Test check raises 400 when user is already banned."""
        ban_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=uuid.uuid4(),
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Banned",
        )

        with patch("app.services.admin.AdminActionRepository.get_by_target_user_id") as mock_get:
            mock_get.return_value = [ban_action]
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service._check_user_not_banned(db, mock_user.id)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "already banned" in exc_info.value.detail.lower()


class TestAdminServiceGet:
    """Test AdminActionService get methods."""

    def test_get_by_id_success(self, admin_service: AdminActionService, mock_action: AdminAction):
        """Test getting admin action by ID."""
        with patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_action
            db = MagicMock(spec=Session)

            result = admin_service.get_by_id(db, mock_action.id)

            assert result == mock_action
            mock_get.assert_called_once_with(db, mock_action.id)

    def test_get_by_id_not_found_raises_404(self, admin_service: AdminActionService):
        """Test getting non-existent action raises 404."""
        with patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            action_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service.get_by_id(db, action_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_by_target_user_id(self, admin_service: AdminActionService, mock_user: User):
        """Test getting admin actions by target user ID."""
        actions = [
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=mock_user.id,
                action_type=AdminActionType.STRIKE,
                reason="Strike 1",
            ),
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=mock_user.id,
                action_type=AdminActionType.BAN,
                reason="Banned",
            ),
        ]

        with patch("app.services.admin.AdminActionRepository.get_by_target_user_id") as mock_get:
            mock_get.return_value = actions
            db = MagicMock(spec=Session)

            result = admin_service.get_by_target_user_id(db, mock_user.id)

            assert result == actions
            mock_get.assert_called_once_with(db, mock_user.id)

    def test_get_by_target_listing_id(self, admin_service: AdminActionService):
        """Test getting admin actions by target listing ID."""
        listing_id = uuid.uuid4()
        actions = [
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=uuid.uuid4(),
                target_listing_id=listing_id,
                action_type=AdminActionType.LISTING_REMOVAL,
                reason="Prohibited item",
            ),
        ]

        with patch("app.services.admin.AdminActionRepository.get_by_target_listing_id") as mock_get:
            mock_get.return_value = actions
            db = MagicMock(spec=Session)

            result = admin_service.get_by_target_listing_id(db, listing_id)

            assert result == actions
            mock_get.assert_called_once_with(db, listing_id)

    def test_get_filtered(self, admin_service: AdminActionService):
        """Test getting filtered admin actions with pagination."""
        filters = AdminActionFilters(
            action_type=AdminActionType.STRIKE,
            skip=0,
            limit=10,
        )
        actions = [
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=uuid.uuid4(),
                action_type=AdminActionType.STRIKE,
                reason="Test",
            ),
        ]

        with (
            patch("app.services.admin.AdminActionRepository.get_filtered") as mock_get_filtered,
            patch("app.services.admin.AdminActionRepository.count_filtered") as mock_count,
        ):
            mock_get_filtered.return_value = actions
            mock_count.return_value = 1
            db = MagicMock(spec=Session)

            result_actions, result_count = admin_service.get_filtered(db, filters)

            assert result_actions == actions
            assert result_count == 1
            mock_get_filtered.assert_called_once_with(db=db, filters=filters)
            mock_count.assert_called_once_with(db=db, filters=filters)


class TestAdminServiceStrike:
    """Test AdminActionService strike creation."""

    def test_create_strike_success(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test creating a strike action."""
        strike_data = AdminActionStrike(reason="Spam listing")
        created_strike = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Spam listing",
        )

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
            patch("app.services.admin.AdminActionRepository.create") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_get_actions.return_value = []  # No existing bans
            mock_create.return_value = created_strike
            db = MagicMock(spec=Session)

            result = admin_service.create_strike(db, mock_admin.id, mock_user.id, strike_data)

            assert result == created_strike
            mock_create.assert_called_once()

    @patch("app.services.admin.settings")
    def test_create_strike_auto_bans_at_threshold(
        self, mock_settings, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test that strike at configured threshold triggers automatic ban."""
        # Configure threshold (default is 3, but testing with explicit value)
        mock_settings.moderation.strike_auto_ban_threshold = 3

        strike_data = AdminActionStrike(reason="Third violation")
        created_strike = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Third violation",
        )

        # Existing 2 strikes
        existing_strikes = [
            AdminAction(
                id=uuid.uuid4(),
                admin_id=mock_admin.id,
                target_user_id=mock_user.id,
                action_type=AdminActionType.STRIKE,
                reason="First",
            ),
            AdminAction(
                id=uuid.uuid4(),
                admin_id=mock_admin.id,
                target_user_id=mock_user.id,
                action_type=AdminActionType.STRIKE,
                reason="Second",
            ),
        ]

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
            patch("app.services.admin.AdminActionRepository.create") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]

            # First call checks for ban (none), second call gets all actions for strike count
            # The count happens AFTER creating the strike, so we return 3 strikes total
            mock_get_actions.side_effect = [[], existing_strikes + [created_strike]]
            mock_create.side_effect = [
                created_strike,
                None,
            ]  # First returns strike, second returns ban
            db = MagicMock(spec=Session)

            result = admin_service.create_strike(db, mock_admin.id, mock_user.id, strike_data)

            # Should create 2 actions: strike + auto-ban
            assert mock_create.call_count == 2

    def test_create_strike_on_banned_user_raises_400(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test creating strike on already banned user raises 400."""
        strike_data = AdminActionStrike(reason="Another violation")
        ban_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Already banned",
        )

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_get_actions.return_value = [ban_action]
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service.create_strike(db, mock_admin.id, mock_user.id, strike_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "already banned" in exc_info.value.detail.lower()


class TestAdminServiceBan:
    """Test AdminActionService ban creation."""

    def test_create_ban_success(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test creating a ban action."""
        ban_data = AdminActionBan(reason="Multiple violations")
        created_ban = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Multiple violations",
        )

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
            patch("app.services.admin.AdminActionRepository.create") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_get_actions.return_value = []  # Not already banned
            mock_create.return_value = created_ban
            db = MagicMock(spec=Session)

            result = admin_service.create_ban(db, mock_admin.id, mock_user.id, ban_data)

            assert result == created_ban
            mock_create.assert_called_once()

    def test_create_ban_on_already_banned_user_raises_400(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test creating ban on already banned user raises 400."""
        ban_data = AdminActionBan(reason="Another ban attempt")
        existing_ban = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Already banned",
        )

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_get_actions.return_value = [existing_ban]
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service.create_ban(db, mock_admin.id, mock_user.id, ban_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "already banned" in exc_info.value.detail.lower()


class TestAdminServiceDelete:
    """Test AdminActionService delete method."""

    def test_delete_action_success(
        self, admin_service: AdminActionService, mock_action: AdminAction
    ):
        """Test deleting an admin action."""
        with (
            patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get,
            patch("app.services.admin.AdminActionRepository.delete") as mock_delete,
        ):
            mock_get.return_value = mock_action
            db = MagicMock(spec=Session)

            admin_service.delete(db, mock_action.id, uuid.uuid4())

            mock_get.assert_called_once_with(db, mock_action.id)
            mock_delete.assert_called_once_with(db, mock_action)

    def test_delete_action_not_found_raises_404(self, admin_service: AdminActionService):
        """Test deleting non-existent action raises 404."""
        with patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            action_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service.delete(db, action_id, uuid.uuid4())

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestAdminServiceListingRemoval:
    """Test AdminActionService listing removal with strike."""

    def test_remove_listing_with_strike_success(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test removing listing with strike creates both actions."""
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id,
            seller_id=mock_user.id,
            title="Bad listing",
            description="Test",
            price=100,
        )

        strike_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Prohibited item",
        )

        listing_removal_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            target_listing_id=listing_id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Prohibited item",
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_actions,
            patch("app.services.admin.AdminActionRepository.create") as mock_create,
            patch("app.services.admin.ListingRepository.delete") as mock_delete,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_get_actions.return_value = []  # Not banned
            # First call creates listing_removal, second creates strike
            mock_create.side_effect = [listing_removal_action, strike_action]
            db = MagicMock(spec=Session)

            result = admin_service.remove_listing_with_strike(
                db, mock_admin.id, listing_id, "Prohibited item"
            )

            assert result.action_type == AdminActionType.LISTING_REMOVAL
            # Verify listing was deleted
            mock_delete.assert_called_once()

    def test_remove_listing_not_found_raises_404(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test removing non-existent listing raises 404."""
        with patch("app.services.admin.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            listing_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service.remove_listing_with_strike(db, mock_admin.id, listing_id, "Test")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestAdminServiceCountStrikes:
    """Test AdminActionService strike counting."""

    def test_count_active_strikes(self, admin_service: AdminActionService, mock_user: User):
        """Test counting strikes for a user."""
        actions = [
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=mock_user.id,
                action_type=AdminActionType.STRIKE,
                reason="First",
            ),
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=mock_user.id,
                action_type=AdminActionType.STRIKE,
                reason="Second",
            ),
            AdminAction(
                id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                target_user_id=mock_user.id,
                action_type=AdminActionType.BAN,  # Not a strike
                reason="Ban",
            ),
        ]

        with patch("app.services.admin.AdminActionRepository.get_by_target_user_id") as mock_get:
            mock_get.return_value = actions
            db = MagicMock(spec=Session)

            count = admin_service._count_active_strikes(db, mock_user.id)

            assert count == 2  # Only strikes, not ban


class TestAdminServiceCreateInternal:
    """Test AdminActionService _create_internal method."""

    def test_create_internal_target_user_not_found(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test _create_internal raises 404 when target user not found."""
        action_data = AdminActionCreate(
            target_user_id=uuid.uuid4(),
            action_type=AdminActionType.STRIKE,
            reason="Test",
            target_listing_id=None,
            expires_at=None,
        )

        with patch("app.services.admin.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = None  # User not found
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service._create_internal(db, mock_admin.id, action_data)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Target user" in exc_info.value.detail

    def test_create_internal_listing_removal_missing_listing_id(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test _create_internal raises 400 for listing_removal without target_listing_id."""
        action_data = AdminActionCreate(
            target_user_id=mock_user.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test",
            target_listing_id=None,  # Missing!
            expires_at=None,
        )

        with patch("app.services.admin.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_user
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service._create_internal(db, mock_admin.id, action_data)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "target_listing_id is required" in exc_info.value.detail


class TestAdminServiceDeleteValidation:
    """Test AdminActionService delete validation."""

    def test_delete_cannot_revoke_own_action(
        self, admin_service: AdminActionService, mock_admin: User
    ):
        """Test admin cannot revoke actions targeting themselves (self-unban prevention)."""
        action = AdminAction(
            id=uuid.uuid4(),
            admin_id=uuid.uuid4(),
            target_user_id=mock_admin.id,  # Action targets the admin trying to revoke
            action_type=AdminActionType.BAN,
            reason="Test",
        )

        with patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get:
            mock_get.return_value = action
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                admin_service.delete(db, action.id, mock_admin.id)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Cannot revoke actions targeting yourself" in exc_info.value.detail


class TestAdminServiceListingRemovalExceptionHandling:
    """Test AdminActionService listing removal exception handling."""

    def test_remove_listing_reraises_non_ban_exceptions(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test that remove_listing_with_strike re-raises exceptions other than 'already banned'."""
        listing = Listing(
            id=uuid.uuid4(),
            seller_id=mock_user.id,
            title="Test",
            description="Test",
            price=100,
            is_active=True,
        )

        # Simulate the strike creation raising a different error (e.g., user not found - 404)
        not_found_exception = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.AdminActionRepository.create") as mock_create_action,
            patch("app.services.admin.AdminActionService._check_user_not_banned") as mock_check,
            patch("app.services.admin.AdminActionService.create_strike") as mock_strike,
        ):
            mock_get_listing.return_value = listing
            mock_create_action.return_value = AdminAction(
                id=uuid.uuid4(),
                admin_id=mock_admin.id,
                target_user_id=mock_user.id,
                action_type=AdminActionType.LISTING_REMOVAL,
                reason="Test",
            )
            mock_check.return_value = None  # User is not banned
            mock_strike.side_effect = not_found_exception  # Raise 404
            db = MagicMock(spec=Session)

            # Should re-raise the 404 exception (not a "already banned" 400)
            with pytest.raises(HTTPException) as exc_info:
                admin_service.remove_listing_with_strike(db, mock_admin.id, listing.id, "Test")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "User not found" in exc_info.value.detail
