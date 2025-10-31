"""
Unit tests for ListingService.

Tests the business logic layer for listing operations.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import Category, Condition
from app.models.listing import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingSearchParams,
    ListingUpdate,
    UserListingsParams,
)
from app.services.listing import ListingService


@pytest.fixture
def listing_service():
    """Create ListingService instance."""
    return ListingService()


@pytest.fixture
def mock_listing():
    """Create a mock listing."""
    seller_id = uuid.uuid4()
    return Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        title="Textbook for Sale",
        description="Great condition",
        price=50.0,
        category=Category.TEXTBOOKS,
        condition=Condition.GOOD,
        is_active=True,
    )


class TestListingServiceGet:
    """Test ListingService get methods."""

    def test_get_by_id_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test getting listing by ID when exists."""
        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_listing
            db = MagicMock(spec=Session)

            result = listing_service.get_by_id(db, mock_listing.id)

            assert result == mock_listing
            mock_get.assert_called_once_with(db, mock_listing.id)

    def test_get_by_id_not_found_raises_404(self, listing_service: ListingService):
        """Test getting listing by ID when doesn't exist raises 404."""
        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)
            listing_id = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                listing_service.get_by_id(db, listing_id)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert str(listing_id) in exc_info.value.detail

    def test_get_by_seller_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test getting listings by seller ID."""
        params = UserListingsParams()
        with (
            patch("app.services.listing.ListingRepository.get_by_seller") as mock_get,
            patch("app.services.listing.ListingRepository.count_by_seller") as mock_count,
        ):
            mock_get.return_value = [mock_listing]
            mock_count.return_value = 1
            db = MagicMock(spec=Session)

            listings, count = listing_service.get_by_seller(db, mock_listing.seller_id, params)

            assert listings == [mock_listing]
            assert count == 1

    def test_get_filtered_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test getting filtered listings."""
        params = ListingSearchParams()
        with (
            patch("app.services.listing.ListingRepository.get_filtered") as mock_get,
            patch("app.services.listing.ListingRepository.count_filtered") as mock_count,
        ):
            mock_get.return_value = [mock_listing]
            mock_count.return_value = 1
            db = MagicMock(spec=Session)

            listings, count = listing_service.get_filtered(db, params)

            assert listings == [mock_listing]
            assert count == 1


class TestListingServiceCreate:
    """Test ListingService create method."""

    def test_create_listing_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test creating a new listing."""
        listing_data = ListingCreate(
            title="Textbook for Sale",
            description="Great condition",
            price=50.0,
            category=Category.TEXTBOOKS,
            condition=Condition.GOOD,
        )

        with patch("app.services.listing.ListingRepository.create") as mock_create:
            mock_create.return_value = mock_listing
            db = MagicMock(spec=Session)

            result = listing_service.create(db, mock_listing.seller_id, listing_data)

            assert result == mock_listing
            mock_create.assert_called_once_with(db, mock_listing.seller_id, listing_data)


class TestListingServiceUpdate:
    """Test ListingService update method."""

    def test_update_listing_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test updating own listing successfully."""
        update_data = ListingUpdate(title="Updated Title")

        with (
            patch("app.services.listing.ListingRepository.get_by_id") as mock_get,
            patch("app.services.listing.ListingRepository.update") as mock_update,
        ):
            mock_get.return_value = mock_listing
            # Just return the same listing since we're mocking
            mock_update.return_value = mock_listing
            db = MagicMock(spec=Session)

            result = listing_service.update(
                db, mock_listing.id, mock_listing.seller_id, update_data
            )

            assert result == mock_listing
            mock_update.assert_called_once()

    def test_update_listing_not_found_raises_404(self, listing_service: ListingService):
        """Test updating non-existent listing raises 404."""
        update_data = ListingUpdate(title="New Title")

        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_service.update(db, uuid.uuid4(), uuid.uuid4(), update_data)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_listing_not_owner_raises_403(
        self, listing_service: ListingService, mock_listing: Listing
    ):
        """Test updating someone else's listing raises 403."""
        update_data = ListingUpdate(title="Hacked Title")

        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_listing
            db = MagicMock(spec=Session)
            different_user = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                listing_service.update(db, mock_listing.id, different_user, update_data)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "owner" in exc_info.value.detail.lower()


class TestListingServiceDelete:
    """Test ListingService delete method."""

    def test_delete_listing_success(self, listing_service: ListingService, mock_listing: Listing):
        """Test deleting own listing successfully."""
        with (
            patch("app.services.listing.ListingRepository.get_by_id") as mock_get,
            patch("app.services.listing.ListingRepository.delete") as mock_delete,
        ):
            mock_get.return_value = mock_listing
            db = MagicMock(spec=Session)

            listing_service.delete(db, mock_listing.id, mock_listing.seller_id)

            mock_delete.assert_called_once_with(db, mock_listing)

    def test_delete_listing_not_found_raises_404(self, listing_service: ListingService):
        """Test deleting non-existent listing raises 404."""
        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_service.delete(db, uuid.uuid4(), uuid.uuid4())

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_listing_not_owner_raises_403(
        self, listing_service: ListingService, mock_listing: Listing
    ):
        """Test deleting someone else's listing raises 403."""
        with patch("app.services.listing.ListingRepository.get_by_id") as mock_get:
            mock_get.return_value = mock_listing
            db = MagicMock(spec=Session)
            different_user = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                listing_service.delete(db, mock_listing.id, different_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "owner" in exc_info.value.detail.lower()
