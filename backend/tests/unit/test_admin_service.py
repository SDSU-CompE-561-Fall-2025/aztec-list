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
        email="admin@example.edu",
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
        email="test@example.edu",
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
            email="admin2@example.edu",
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
        with patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban:
            mock_has_ban.return_value = None
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

        with patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban:
            mock_has_ban.return_value = ban_action
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
        action_id = uuid.uuid4()
        admin_id = uuid.uuid4()
        target_id = uuid.uuid4()

        # Repository now returns tuples
        repo_results = [
            (
                AdminAction(
                    id=action_id,
                    admin_id=admin_id,
                    target_user_id=target_id,
                    action_type=AdminActionType.STRIKE,
                    reason="Test",
                ),
                "admin_user",  # admin_username
                "target_user",  # target_username
            )
        ]

        with (
            patch("app.services.admin.AdminActionRepository.get_filtered") as mock_get_filtered,
            patch("app.services.admin.AdminActionRepository.count_filtered") as mock_count,
        ):
            mock_get_filtered.return_value = repo_results
            mock_count.return_value = 1
            db = MagicMock(spec=Session)

            result_actions, result_count = admin_service.get_filtered(db, filters)

            # Service now returns list of dicts
            assert isinstance(result_actions, list)
            assert len(result_actions) == 1
            assert result_actions[0]["id"] == action_id
            assert result_actions[0]["admin_username"] == "admin_user"
            assert result_actions[0]["target_username"] == "target_user"
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
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.count_strikes") as mock_count,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_has_ban.return_value = None  # No existing ban
            mock_count.return_value = 0  # No existing strikes
            mock_create.return_value = created_strike
            db = MagicMock(spec=Session)

            # create_strike now returns (strike_action, strike_count, auto_ban_triggered)
            result_strike, strike_count, auto_ban = admin_service.create_strike(
                db, mock_admin.id, mock_user.id, strike_data
            )

            assert result_strike == created_strike
            assert strike_count == 0
            assert auto_ban is False
            mock_create.assert_called_once()
            db.commit.assert_called_once()

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

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.count_strikes") as mock_count,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_has_ban.return_value = None  # No existing ban
            # After creating the strike, user will have 3 strikes
            mock_count.return_value = 3
            mock_create.side_effect = [
                created_strike,
                None,
            ]  # First returns strike, second returns ban
            db = MagicMock(spec=Session)

            result = admin_service.create_strike(db, mock_admin.id, mock_user.id, strike_data)

            # Should create 2 actions: strike + auto-ban
            assert mock_create.call_count == 2
            db.commit.assert_called_once()

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

    def test_create_strike_rollback_on_exception(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test that create_strike rolls back transaction on exception."""
        strike_data = AdminActionStrike(reason="Test violation")

        with (
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.ensure_can_moderate_user"),
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_has_ban.return_value = None  # No existing ban
            mock_create.side_effect = Exception("Database error")
            db = MagicMock(spec=Session)

            with pytest.raises(Exception) as exc_info:
                admin_service.create_strike(db, mock_admin.id, mock_user.id, strike_data)

            assert "Database error" in str(exc_info.value)
            db.rollback.assert_called_once()
            db.commit.assert_not_called()


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
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.create") as mock_create,
        ):
            mock_get_user.side_effect = [mock_user, mock_admin]
            mock_has_ban.return_value = None  # Not already banned
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
            patch("app.services.admin.AdminActionRepository.delete_no_commit") as mock_delete,
        ):
            mock_get.return_value = mock_action
            db = MagicMock(spec=Session)

            admin_service.delete(db, mock_action.id, uuid.uuid4())

            mock_get.assert_called_once_with(db, mock_action.id)
            mock_delete.assert_called_once_with(db, mock_action)
            db.commit.assert_called_once()

    def test_delete_action_not_found_raises_404(self, admin_service: AdminActionService):
        """Test deleting non-existent action raises 404."""
        with patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            action_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                admin_service.delete(db, action_id, uuid.uuid4())

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_auto_ban_removes_most_recent_strike(
        self, admin_service: AdminActionService, mock_user: User, mock_admin: User
    ):
        """Test that deleting an auto-ban also removes the most recent strike."""
        # Create an auto-ban action with the specific reason pattern
        auto_ban = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Automatic permanent ban: 3 strikes accumulated. Latest: Spam",
        )

        # Create mock strikes
        strike1 = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Strike 1",
        )
        strike2 = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.STRIKE,
            reason="Strike 2",
        )

        with (
            patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get,
            patch(
                "app.services.admin.AdminActionRepository.get_by_target_user_id"
            ) as mock_get_user_actions,
            patch("app.services.admin.AdminActionRepository.delete_no_commit") as mock_delete,
        ):
            mock_get.return_value = auto_ban
            mock_get_user_actions.return_value = [strike1, strike2]
            db = MagicMock(spec=Session)

            admin_service.delete(db, auto_ban.id, uuid.uuid4())

            # Should delete both the auto-ban and the most recent strike
            assert mock_delete.call_count == 2
            calls = mock_delete.call_args_list
            # First call should delete the most recent strike
            assert calls[0][0][1] == strike1
            # Second call should delete the ban itself
            assert calls[1][0][1] == auto_ban
            db.commit.assert_called_once()

    def test_delete_regular_ban_does_not_remove_strikes(
        self, admin_service: AdminActionService, mock_user: User, mock_admin: User
    ):
        """Test that deleting a regular (non-auto) ban does not remove strikes."""
        regular_ban = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.BAN,
            reason="Manual ban for harassment",
        )

        with (
            patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get,
            patch("app.services.admin.AdminActionRepository.delete_no_commit") as mock_delete,
        ):
            mock_get.return_value = regular_ban
            db = MagicMock(spec=Session)

            admin_service.delete(db, regular_ban.id, uuid.uuid4())

            # Should only delete the ban, not check for strikes
            mock_delete.assert_called_once_with(db, regular_ban)
            db.commit.assert_called_once()

    def test_delete_action_rollback_on_exception(
        self, admin_service: AdminActionService, mock_action: AdminAction
    ):
        """Test that delete rolls back transaction on exception."""
        with (
            patch("app.services.admin.AdminActionRepository.get_by_id") as mock_get,
            patch("app.services.admin.AdminActionRepository.delete_no_commit") as mock_delete,
        ):
            mock_get.return_value = mock_action
            mock_delete.side_effect = Exception("Database error")
            db = MagicMock(spec=Session)

            with pytest.raises(Exception) as exc_info:
                admin_service.delete(db, mock_action.id, uuid.uuid4())

            assert "Database error" in str(exc_info.value)
            db.rollback.assert_called_once()
            db.commit.assert_not_called()


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
            reason="Listing removed: Prohibited item",
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
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.AdminActionRepository.count_strikes") as mock_count_strikes,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.delete_listing_images") as mock_delete_images,
        ):
            mock_get_listing.return_value = mock_listing
            mock_get_user.return_value = mock_user
            mock_has_ban.return_value = None  # Not banned
            mock_count_strikes.return_value = 1  # Below threshold
            # First call creates removal_action, second creates strike
            mock_create.side_effect = [listing_removal_action, strike_action]
            db = MagicMock(spec=Session)

            result = admin_service.remove_listing_with_strike(
                db, mock_admin.id, listing_id, "Prohibited item"
            )

            assert result.action_type == AdminActionType.LISTING_REMOVAL
            # Verify listing was deleted
            mock_delete.assert_called_once_with(db, mock_listing)
            # Verify commit was called
            db.commit.assert_called_once()
            # Verify images deleted after commit
            mock_delete_images.assert_called_once_with(listing_id)

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

    def test_remove_listing_with_already_banned_user(
        self, admin_service: AdminActionService, mock_admin: User, mock_user: User
    ):
        """Test that remove_listing_with_strike skips strike creation for already banned users."""
        listing = Listing(
            id=uuid.uuid4(),
            seller_id=mock_user.id,
            title="Test",
            description="Test",
            price=100,
            is_active=True,
        )

        removal_action = AdminAction(
            id=uuid.uuid4(),
            admin_id=mock_admin.id,
            target_user_id=mock_user.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test",
            target_listing_id=listing.id,
        )

        with (
            patch("app.services.admin.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.admin.UserRepository.get_by_id") as mock_get_user,
            patch("app.services.admin.AdminActionRepository.has_active_ban") as mock_has_ban,
            patch("app.services.admin.ListingRepository.delete_no_commit") as mock_delete,
            patch("app.services.admin.delete_listing_images") as mock_delete_images,
            patch("app.services.admin.AdminActionRepository.create_no_commit") as mock_create,
        ):
            mock_get_listing.return_value = listing
            mock_get_user.return_value = mock_user
            mock_has_ban.return_value = AdminAction(  # User is already banned
                id=uuid.uuid4(),
                admin_id=mock_admin.id,
                target_user_id=mock_user.id,
                action_type=AdminActionType.BAN,
                reason="Banned",
            )
            mock_create.return_value = removal_action
            db = MagicMock(spec=Session)

            result = admin_service.remove_listing_with_strike(db, mock_admin.id, listing.id, "Test")

            # Should create removal action but NOT create strike
            assert result.action_type == AdminActionType.LISTING_REMOVAL
            # Verify listing was deleted
            mock_delete.assert_called_once_with(db, listing)
            # Verify only ONE create call (removal action, no strike)
            assert mock_create.call_count == 1
            # Verify commit was called
            db.commit.assert_called_once()
            # Verify images deleted
            mock_delete_images.assert_called_once_with(listing.id)
