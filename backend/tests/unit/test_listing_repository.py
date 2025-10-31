"""
Unit tests for ListingRepository.

Tests the data access layer for listing operations.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.enums import Category, Condition, ListingSortOrder
from app.models.listing import Listing
from app.models.user import User
from app.repository.listing import ListingRepository
from app.schemas.listing import (
    ListingCreate,
    ListingSearchParams,
    ListingUpdate,
    UserListingsParams,
)


@pytest.fixture
def test_listing(db_session: Session, test_user: User) -> Listing:
    """Create a test listing."""
    listing = Listing(
        seller_id=test_user.id,
        title="Test Listing",
        description="Test Description",
        price=Decimal("100.00"),
        category=Category.ELECTRONICS,
        condition=Condition.NEW,
        is_active=True,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


@pytest.fixture
def inactive_listing(db_session: Session, test_user: User) -> Listing:
    """Create an inactive test listing."""
    listing = Listing(
        seller_id=test_user.id,
        title="Inactive Listing",
        description="Inactive Description",
        price=Decimal("50.00"),
        category=Category.TEXTBOOKS,
        condition=Condition.GOOD,
        is_active=False,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


class TestListingRepositoryGet:
    """Test ListingRepository get methods."""

    def test_get_by_id_found(self, db_session: Session, test_listing: Listing):
        """Test getting listing by ID when exists."""
        result = ListingRepository.get_by_id(db_session, test_listing.id)

        assert result is not None
        assert result.id == test_listing.id
        assert result.title == test_listing.title

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting listing by ID when doesn't exist."""
        random_id = uuid.uuid4()
        result = ListingRepository.get_by_id(db_session, random_id)

        assert result is None

    def test_get_by_seller(self, db_session: Session, test_user: User, test_listing: Listing):
        """Test getting listings by seller."""
        params = UserListingsParams(
            include_inactive=False, sort=ListingSortOrder.RECENT, offset=0, limit=10
        )
        results = ListingRepository.get_by_seller(db_session, test_user.id, params)

        assert len(results) == 1
        assert results[0].id == test_listing.id
        assert results[0].seller_id == test_user.id

    def test_get_by_seller_with_inactive(
        self, db_session: Session, test_user: User, test_listing: Listing, inactive_listing: Listing
    ):
        """Test getting listings by seller including inactive ones."""
        params = UserListingsParams(
            include_inactive=True, sort=ListingSortOrder.RECENT, offset=0, limit=10
        )
        results = ListingRepository.get_by_seller(db_session, test_user.id, params)

        assert len(results) == 2
        listing_ids = {listing.id for listing in results}
        assert test_listing.id in listing_ids
        assert inactive_listing.id in listing_ids

    def test_get_by_seller_excludes_inactive_by_default(
        self, db_session: Session, test_user: User, test_listing: Listing, inactive_listing: Listing
    ):
        """Test that inactive listings are excluded by default."""
        params = UserListingsParams(
            include_inactive=False, sort=ListingSortOrder.RECENT, offset=0, limit=10
        )
        results = ListingRepository.get_by_seller(db_session, test_user.id, params)

        assert len(results) == 1
        assert results[0].id == test_listing.id

    def test_count_by_seller(self, db_session: Session, test_user: User, test_listing: Listing):
        """Test counting listings by seller."""
        params = UserListingsParams(include_inactive=False, sort=ListingSortOrder.RECENT)
        count = ListingRepository.count_by_seller(db_session, test_user.id, params)

        assert count == 1

    def test_count_by_seller_with_inactive(
        self, db_session: Session, test_user: User, test_listing: Listing, inactive_listing: Listing
    ):
        """Test counting listings by seller including inactive."""
        params = UserListingsParams(include_inactive=True, sort=ListingSortOrder.RECENT)
        count = ListingRepository.count_by_seller(db_session, test_user.id, params)

        assert count == 2


class TestListingRepositorySearch:
    """Test ListingRepository search and filter methods."""

    def test_get_filtered_no_params(self, db_session: Session, test_listing: Listing):
        """Test getting all active listings with no filters."""
        params = ListingSearchParams()
        results = ListingRepository.get_filtered(db_session, params)

        assert len(results) >= 1
        assert any(listing.id == test_listing.id for listing in results)

    def test_get_filtered_by_search_text_title(self, db_session: Session, test_listing: Listing):
        """Test filtering by search text matching title."""
        params = ListingSearchParams(search_text="Test")
        results = ListingRepository.get_filtered(db_session, params)

        assert len(results) >= 1
        assert any(listing.id == test_listing.id for listing in results)

    def test_get_filtered_by_search_text_description(
        self, db_session: Session, test_listing: Listing
    ):
        """Test filtering by search text matching description."""
        params = ListingSearchParams(search_text="Description")
        results = ListingRepository.get_filtered(db_session, params)

        assert len(results) >= 1
        assert any(listing.id == test_listing.id for listing in results)

    def test_get_filtered_by_category(self, db_session: Session, test_listing: Listing):
        """Test filtering by category."""
        params = ListingSearchParams(category=Category.ELECTRONICS)
        results = ListingRepository.get_filtered(db_session, params)

        assert len(results) >= 1
        assert all(listing.category == Category.ELECTRONICS for listing in results)

    def test_get_filtered_by_min_price(self, db_session: Session, test_listing: Listing):
        """Test filtering by minimum price."""
        params = ListingSearchParams(min_price=Decimal("50.00"))
        results = ListingRepository.get_filtered(db_session, params)

        assert all(listing.price >= Decimal("50.00") for listing in results)

    def test_get_filtered_by_max_price(self, db_session: Session, test_listing: Listing):
        """Test filtering by maximum price."""
        params = ListingSearchParams(max_price=Decimal("150.00"))
        results = ListingRepository.get_filtered(db_session, params)

        assert all(listing.price <= Decimal("150.00") for listing in results)

    def test_get_filtered_by_condition(self, db_session: Session, test_listing: Listing):
        """Test filtering by condition."""
        params = ListingSearchParams(condition=Condition.NEW)
        results = ListingRepository.get_filtered(db_session, params)

        assert all(listing.condition == Condition.NEW for listing in results)

    def test_get_filtered_by_seller_id(
        self, db_session: Session, test_user: User, test_listing: Listing
    ):
        """Test filtering by seller ID."""
        params = ListingSearchParams(seller_id=test_user.id)
        results = ListingRepository.get_filtered(db_session, params)

        assert all(listing.seller_id == test_user.id for listing in results)

    def test_get_filtered_excludes_inactive(
        self, db_session: Session, test_listing: Listing, inactive_listing: Listing
    ):
        """Test that search only returns active listings."""
        params = ListingSearchParams()
        results = ListingRepository.get_filtered(db_session, params)

        listing_ids = {listing.id for listing in results}
        assert test_listing.id in listing_ids
        assert inactive_listing.id not in listing_ids

    def test_count_filtered(self, db_session: Session, test_listing: Listing):
        """Test counting filtered listings."""
        params = ListingSearchParams()
        count = ListingRepository.count_filtered(db_session, params)

        assert count >= 1


class TestListingRepositorySorting:
    """Test ListingRepository sorting functionality."""

    def test_sort_by_recent(self, db_session: Session, test_user: User):
        """Test sorting by most recent."""
        # Create listings in specific order
        old_listing = Listing(
            seller_id=test_user.id,
            title="Old Listing",
            description="Old",
            price=Decimal("100.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        new_listing = Listing(
            seller_id=test_user.id,
            title="New Listing",
            description="New",
            price=Decimal("100.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        db_session.add(old_listing)
        db_session.commit()
        db_session.add(new_listing)
        db_session.commit()

        params = ListingSearchParams(sort=ListingSortOrder.RECENT)
        results = ListingRepository.get_filtered(db_session, params)

        # New listing should come first
        assert results[0].id == new_listing.id

    def test_sort_by_price_asc(self, db_session: Session, test_user: User):
        """Test sorting by price ascending."""
        cheap = Listing(
            seller_id=test_user.id,
            title="Cheap",
            description="Cheap",
            price=Decimal("10.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        expensive = Listing(
            seller_id=test_user.id,
            title="Expensive",
            description="Expensive",
            price=Decimal("200.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        db_session.add_all([expensive, cheap])
        db_session.commit()

        params = ListingSearchParams(sort=ListingSortOrder.PRICE_ASC)
        results = ListingRepository.get_filtered(db_session, params)

        # Cheap should come first
        assert results[0].price == Decimal("10.00")

    def test_sort_by_price_desc(self, db_session: Session, test_user: User):
        """Test sorting by price descending."""
        cheap = Listing(
            seller_id=test_user.id,
            title="Cheap",
            description="Cheap",
            price=Decimal("10.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        expensive = Listing(
            seller_id=test_user.id,
            title="Expensive",
            description="Expensive",
            price=Decimal("200.00"),
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        db_session.add_all([cheap, expensive])
        db_session.commit()

        params = ListingSearchParams(sort=ListingSortOrder.PRICE_DESC)
        results = ListingRepository.get_filtered(db_session, params)

        # Expensive should come first
        assert results[0].price == Decimal("200.00")


class TestListingRepositoryCreate:
    """Test ListingRepository create method."""

    def test_create_listing_success(self, db_session: Session, test_user: User):
        """Test creating a listing."""
        listing_data = ListingCreate(
            title="New Listing",
            description="New Description",
            price=Decimal("75.00"),
            category=Category.FURNITURE,
            condition=Condition.LIKE_NEW,
        )
        result = ListingRepository.create(db_session, test_user.id, listing_data)

        assert result.id is not None
        assert result.seller_id == test_user.id
        assert result.title == "New Listing"
        assert result.price == Decimal("75.00")
        assert result.category == Category.FURNITURE
        assert result.condition == Condition.LIKE_NEW
        assert result.is_active is True

    def test_create_listing_with_optional_fields(self, db_session: Session, test_user: User):
        """Test creating listing successfully."""
        listing_data = ListingCreate(
            title="Complete Listing",
            description="Has all fields",
            price=Decimal("50.00"),
            category=Category.ELECTRONICS,
            condition=Condition.GOOD,
        )
        result = ListingRepository.create(db_session, test_user.id, listing_data)

        assert result.id is not None
        assert result.title == "Complete Listing"
        assert result.price == Decimal("50.00")
        assert result.thumbnail_url is None  # Thumbnail set separately via images


class TestListingRepositoryUpdate:
    """Test ListingRepository update method."""

    def test_update_listing_title(self, db_session: Session, test_listing: Listing):
        """Test updating listing title."""
        update_data = ListingUpdate(title="Updated Title")
        result = ListingRepository.update(db_session, test_listing, update_data)

        assert result.title == "Updated Title"
        assert result.id == test_listing.id

    def test_update_listing_price(self, db_session: Session, test_listing: Listing):
        """Test updating listing price."""
        update_data = ListingUpdate(price=Decimal("125.00"))
        result = ListingRepository.update(db_session, test_listing, update_data)

        assert result.price == Decimal("125.00")

    def test_update_listing_multiple_fields(self, db_session: Session, test_listing: Listing):
        """Test updating multiple listing fields."""
        update_data = ListingUpdate(
            title="Multi Update",
            description="Updated description",
            price=Decimal("99.99"),
            condition=Condition.GOOD,
        )
        result = ListingRepository.update(db_session, test_listing, update_data)

        assert result.title == "Multi Update"
        assert result.description == "Updated description"
        assert result.price == Decimal("99.99")
        assert result.condition == Condition.GOOD

    def test_update_listing_deactivate(self, db_session: Session, test_listing: Listing):
        """Test deactivating a listing."""
        update_data = ListingUpdate(is_active=False)
        result = ListingRepository.update(db_session, test_listing, update_data)

        assert result.is_active is False


class TestListingRepositoryDelete:
    """Test ListingRepository delete method."""

    def test_delete_listing(self, db_session: Session, test_listing: Listing):
        """Test deleting a listing."""
        listing_id = test_listing.id

        ListingRepository.delete(db_session, test_listing)

        # Verify listing is deleted
        deleted_listing = ListingRepository.get_by_id(db_session, listing_id)
        assert deleted_listing is None

    def test_delete_listing_removes_from_session(self, db_session: Session, test_listing: Listing):
        """Test that deleted listing is removed from session."""
        ListingRepository.delete(db_session, test_listing)

        # Listing should not be in session
        assert test_listing not in db_session
