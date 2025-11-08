"""
Unit tests for AdminActionRepository.

Tests the data access layer for admin action operations.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.enums import AdminActionType, Category, Condition
from app.models.admin import AdminAction
from app.models.listing import Listing
from app.models.user import User
from app.repository.admin import AdminActionRepository
from app.schemas.admin import AdminActionCreate, AdminActionFilters


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an admin user for testing."""
    from app.core.auth import get_password_hash
    from app.core.enums import UserRole

    user = User(
        username="admin_user",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def target_listing(db_session: Session, test_user: User) -> Listing:
    """Create a target listing for admin actions."""
    listing = Listing(
        seller_id=test_user.id,
        title="Target Listing",
        description="For admin action",
        price=Decimal("100.00"),
        category=Category.ELECTRONICS,
        condition=Condition.NEW,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


@pytest.fixture
def test_admin_action(
    db_session: Session, admin_user: User, test_user: User, target_listing: Listing
) -> AdminAction:
    """Create a test admin action."""
    action = AdminAction(
        admin_id=admin_user.id,
        target_user_id=test_user.id,
        target_listing_id=target_listing.id,
        action_type=AdminActionType.STRIKE,
        reason="Test violation",
    )
    db_session.add(action)
    db_session.commit()
    db_session.refresh(action)
    return action


class TestAdminActionRepositoryGet:
    """Test AdminActionRepository get methods."""

    def test_get_by_id_found(self, db_session: Session, test_admin_action: AdminAction):
        """Test getting admin action by ID when exists."""
        result = AdminActionRepository.get_by_id(db_session, test_admin_action.id)

        assert result is not None
        assert result.id == test_admin_action.id
        assert result.action_type == test_admin_action.action_type

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting admin action by ID when doesn't exist."""
        random_id = uuid.uuid4()
        result = AdminActionRepository.get_by_id(db_session, random_id)

        assert result is None

    def test_get_by_target_user_id(
        self, db_session: Session, test_user: User, test_admin_action: AdminAction
    ):
        """Test getting actions by target user ID."""
        results = AdminActionRepository.get_by_target_user_id(db_session, test_user.id)

        assert len(results) >= 1
        assert any(action.id == test_admin_action.id for action in results)
        assert all(action.target_user_id == test_user.id for action in results)

    def test_get_by_admin_id(
        self, db_session: Session, admin_user: User, test_admin_action: AdminAction
    ):
        """Test getting actions by admin ID."""
        results = AdminActionRepository.get_by_admin_id(db_session, admin_user.id)

        assert len(results) >= 1
        assert any(action.id == test_admin_action.id for action in results)
        assert all(action.admin_id == admin_user.id for action in results)

    def test_get_by_target_listing_id(
        self, db_session: Session, target_listing: Listing, test_admin_action: AdminAction
    ):
        """Test getting actions by target listing ID."""
        results = AdminActionRepository.get_by_target_listing_id(db_session, target_listing.id)

        assert len(results) >= 1
        assert any(action.id == test_admin_action.id for action in results)
        assert all(action.target_listing_id == target_listing.id for action in results)

    def test_get_by_action_type(self, db_session: Session, test_admin_action: AdminAction):
        """Test getting actions by action type."""
        results = AdminActionRepository.get_by_action_type(db_session, AdminActionType.STRIKE)

        assert len(results) >= 1
        assert all(action.action_type == AdminActionType.STRIKE for action in results)

    def test_has_active_ban_with_ban(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test has_active_ban returns ban when user is banned."""
        # Create a ban action
        ban_action = AdminAction(
            admin_id=admin_user.id,
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.BAN,
            reason="Test ban",
        )
        db_session.add(ban_action)
        db_session.commit()

        result = AdminActionRepository.has_active_ban(db_session, test_user.id)

        assert result is not None
        assert result.id == ban_action.id
        assert result.action_type == AdminActionType.BAN

    def test_has_active_ban_without_ban(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test has_active_ban returns None when user is not banned."""
        # Create non-ban actions
        strike_action = AdminAction(
            admin_id=admin_user.id,
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.STRIKE,
            reason="Test strike",
        )
        removal_action = AdminAction(
            admin_id=admin_user.id,
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test listing removal",
        )
        db_session.add_all([strike_action, removal_action])
        db_session.commit()

        result = AdminActionRepository.has_active_ban(db_session, test_user.id)

        assert result is None

    def test_has_active_ban_no_actions(self, db_session: Session):
        """Test has_active_ban returns None when user has no actions."""
        random_user_id = uuid.uuid4()
        result = AdminActionRepository.has_active_ban(db_session, random_user_id)

        assert result is None

    def test_count_strikes_with_strikes(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test count_strikes returns correct count when user has strikes."""
        # Create multiple strikes
        for i in range(3):
            strike_action = AdminAction(
                admin_id=admin_user.id,
                target_user_id=test_user.id,
                target_listing_id=target_listing.id,
                action_type=AdminActionType.STRIKE,
                reason=f"Strike {i}",
            )
            db_session.add(strike_action)
        # Add a ban to ensure it's not counted
        ban_action = AdminAction(
            admin_id=admin_user.id,
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.BAN,
            reason="Ban",
        )
        db_session.add(ban_action)
        db_session.commit()

        result = AdminActionRepository.count_strikes(db_session, test_user.id)

        assert result == 3

    def test_count_strikes_no_strikes(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test count_strikes returns 0 when user has no strikes."""
        # Create non-strike actions
        ban_action = AdminAction(
            admin_id=admin_user.id,
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.BAN,
            reason="Ban",
        )
        db_session.add(ban_action)
        db_session.commit()

        result = AdminActionRepository.count_strikes(db_session, test_user.id)

        assert result == 0

    def test_count_strikes_no_actions(self, db_session: Session):
        """Test count_strikes returns 0 when user has no actions."""
        random_user_id = uuid.uuid4()
        result = AdminActionRepository.count_strikes(db_session, random_user_id)

        assert result == 0

    def test_get_all(self, db_session: Session, test_admin_action: AdminAction):
        """Test getting all admin actions with pagination."""
        results = AdminActionRepository.get_all(db_session, offset=0, limit=10)

        assert len(results) >= 1
        assert any(action.id == test_admin_action.id for action in results)

    def test_get_all_pagination(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test pagination in get_all."""
        # Create multiple actions
        actions = [
            AdminAction(
                admin_id=admin_user.id,
                target_user_id=test_user.id,
                target_listing_id=target_listing.id,
                action_type=AdminActionType.STRIKE,
                reason=f"Violation {i}",
            )
            for i in range(5)
        ]
        db_session.add_all(actions)
        db_session.commit()

        # Get first 2
        page1 = AdminActionRepository.get_all(db_session, offset=0, limit=2)
        assert len(page1) == 2

        # Get next 2
        page2 = AdminActionRepository.get_all(db_session, offset=2, limit=2)
        assert len(page2) == 2

        # Ensure different results
        page1_ids = {action.id for action in page1}
        page2_ids = {action.id for action in page2}
        assert page1_ids.isdisjoint(page2_ids)


class TestAdminActionRepositoryFilters:
    """Test AdminActionRepository filtering functionality."""

    def test_get_filtered_by_action_type(self, db_session: Session, test_admin_action: AdminAction):
        """Test filtering by action type."""
        filters = AdminActionFilters(action_type=AdminActionType.STRIKE)
        results = AdminActionRepository.get_filtered(db_session, filters)

        assert all(action.action_type == AdminActionType.STRIKE for action in results)

    def test_get_filtered_by_admin_id(
        self, db_session: Session, admin_user: User, test_admin_action: AdminAction
    ):
        """Test filtering by admin ID."""
        filters = AdminActionFilters(admin_id=admin_user.id)
        results = AdminActionRepository.get_filtered(db_session, filters)

        assert all(action.admin_id == admin_user.id for action in results)

    def test_get_filtered_by_target_user_id(
        self, db_session: Session, test_user: User, test_admin_action: AdminAction
    ):
        """Test filtering by target user ID."""
        filters = AdminActionFilters(target_user_id=test_user.id)
        results = AdminActionRepository.get_filtered(db_session, filters)

        assert all(action.target_user_id == test_user.id for action in results)

    def test_get_filtered_by_target_listing_id(
        self, db_session: Session, target_listing: Listing, test_admin_action: AdminAction
    ):
        """Test filtering by target listing ID."""
        filters = AdminActionFilters(target_listing_id=target_listing.id)
        results = AdminActionRepository.get_filtered(db_session, filters)

        assert all(action.target_listing_id == target_listing.id for action in results)

    def test_get_filtered_multiple_criteria(
        self,
        db_session: Session,
        admin_user: User,
        test_user: User,
        test_admin_action: AdminAction,
    ):
        """Test filtering with multiple criteria."""
        filters = AdminActionFilters(
            action_type=AdminActionType.STRIKE,
            admin_id=admin_user.id,
            target_user_id=test_user.id,
        )
        results = AdminActionRepository.get_filtered(db_session, filters)

        assert all(action.action_type == AdminActionType.STRIKE for action in results)
        assert all(action.admin_id == admin_user.id for action in results)
        assert all(action.target_user_id == test_user.id for action in results)

    def test_count_filtered(self, db_session: Session, test_admin_action: AdminAction):
        """Test counting filtered results."""
        filters = AdminActionFilters(action_type=AdminActionType.STRIKE)
        count = AdminActionRepository.count_filtered(db_session, filters)

        assert count >= 1

    def test_get_filtered_by_date_range(self, db_session: Session, test_admin_action: AdminAction):
        """Test filtering by date range."""
        from datetime import datetime, timedelta, timezone

        # Test from_date filter
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        filters = AdminActionFilters(from_date=yesterday)
        results = AdminActionRepository.get_filtered(db_session, filters)
        assert len(results) >= 1

        # Test to_date filter
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        filters = AdminActionFilters(to_date=tomorrow)
        results = AdminActionRepository.get_filtered(db_session, filters)
        assert len(results) >= 1

        # Test both from_date and to_date
        filters = AdminActionFilters(from_date=yesterday, to_date=tomorrow)
        results = AdminActionRepository.get_filtered(db_session, filters)
        assert len(results) >= 1

    def test_count_filtered_with_date_range(
        self, db_session: Session, test_admin_action: AdminAction
    ):
        """Test counting filtered results with date range."""
        from datetime import datetime, timedelta, timezone

        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)

        filters = AdminActionFilters(from_date=yesterday, to_date=tomorrow)
        count = AdminActionRepository.count_filtered(db_session, filters)
        assert count >= 1

    def test_get_filtered_with_target_listing_id_in_filters(
        self, db_session: Session, target_listing: Listing, admin_user: User, test_user: User
    ):
        """Test get_filtered applies target_listing_id filter correctly."""
        # Create an action with target_listing_id
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test",
        )
        AdminActionRepository.create(db_session, admin_user.id, action_data)

        filters = AdminActionFilters(target_listing_id=target_listing.id)
        results = AdminActionRepository.get_filtered(db_session, filters)
        assert len(results) >= 1

    def test_count_filtered_with_target_listing_id(
        self, db_session: Session, target_listing: Listing, admin_user: User, test_user: User
    ):
        """Test count_filtered applies target_listing_id filter correctly."""
        # Create an action with target_listing_id
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Test",
        )
        AdminActionRepository.create(db_session, admin_user.id, action_data)

        filters = AdminActionFilters(target_listing_id=target_listing.id)
        count = AdminActionRepository.count_filtered(db_session, filters)
        assert count >= 1


class TestAdminActionRepositoryCreate:
    """Test AdminActionRepository create method."""

    def test_create_strike_action(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test creating a strike action."""
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.STRIKE,
            reason="Spam listing",
        )
        result = AdminActionRepository.create(db_session, admin_user.id, action_data)

        assert result.id is not None
        assert result.admin_id == admin_user.id
        assert result.target_user_id == test_user.id
        assert result.target_listing_id == target_listing.id
        assert result.action_type == AdminActionType.STRIKE
        assert result.reason == "Spam listing"

    def test_create_ban_action(self, db_session: Session, admin_user: User, test_user: User):
        """Test creating a ban action."""
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            action_type=AdminActionType.BAN,
            reason="Multiple violations",
        )
        result = AdminActionRepository.create(db_session, admin_user.id, action_data)

        assert result.action_type == AdminActionType.BAN
        assert result.target_listing_id is None

    def test_create_listing_removal_action(
        self, db_session: Session, admin_user: User, test_user: User, target_listing: Listing
    ):
        """Test creating a listing removal action."""
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            target_listing_id=target_listing.id,
            action_type=AdminActionType.LISTING_REMOVAL,
            reason="Prohibited item",
        )
        result = AdminActionRepository.create(db_session, admin_user.id, action_data)

        assert result.action_type == AdminActionType.LISTING_REMOVAL
        assert result.target_listing_id == target_listing.id

    def test_create_action_without_notes(
        self, db_session: Session, admin_user: User, test_user: User
    ):
        """Test creating action without optional notes field."""
        action_data = AdminActionCreate(
            target_user_id=test_user.id,
            action_type=AdminActionType.BAN,
            reason="Ban reason",
        )
        result = AdminActionRepository.create(db_session, admin_user.id, action_data)

        assert result.id is not None
        assert result.reason == "Ban reason"


class TestAdminActionRepositoryDelete:
    """Test AdminActionRepository delete method."""

    def test_delete_action(self, db_session: Session, test_admin_action: AdminAction):
        """Test deleting an admin action."""
        action_id = test_admin_action.id

        AdminActionRepository.delete(db_session, test_admin_action)

        # Verify action is deleted
        deleted_action = AdminActionRepository.get_by_id(db_session, action_id)
        assert deleted_action is None

    def test_delete_action_removes_from_session(
        self, db_session: Session, test_admin_action: AdminAction
    ):
        """Test that deleted action is removed from session."""
        AdminActionRepository.delete(db_session, test_admin_action)

        assert test_admin_action not in db_session
