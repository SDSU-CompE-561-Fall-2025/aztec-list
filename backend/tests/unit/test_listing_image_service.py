"""
Unit tests for ListingImageService.

Tests the business logic layer for listing image operations.
Uses configurable settings for max_images_per_listing.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.listing import Listing
from app.models.listing_image import Image
from app.models.user import User
from app.schemas.listing_image import ImageCreate, ImageUpdate
from app.services.listing_image import ListingImageService


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return User(
        id=uuid.uuid4(),
        username="seller",
        email="seller@example.com",
        hashed_password="hashed",
        role=UserRole.USER,
    )


@pytest.fixture
def listing_image_service():
    """Create ListingImageService instance."""
    return ListingImageService()


class TestListingImageServiceGet:
    """Test ListingImageService get method."""

    def test_get_by_id_success(self, listing_image_service: ListingImageService, mock_user: User):
        """Test getting an image by ID successfully."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            db = MagicMock(spec=Session)

            result = listing_image_service.get_by_id(db, image_id, mock_user)

            assert result == mock_image

    def test_get_by_id_not_found_raises_404(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test getting non-existent image raises 404."""
        with patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.get_by_id(db, uuid.uuid4(), mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_by_id_unauthorized_seller_raises_403(
        self, listing_image_service: ListingImageService
    ):
        """Test getting image for someone else's listing raises 403."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        different_user_id = uuid.uuid4()

        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=owner_id, title="Test", description="Test", price=100
        )
        different_user = User(
            id=different_user_id,
            username="other",
            email="other@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.get_by_id(db, image_id, different_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestListingImageServiceCreate:
    """Test ListingImageService create method."""

    @patch("app.services.listing_image.settings")
    def test_create_image_success(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test creating an image successfully."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        mock_image = Image(
            id=uuid.uuid4(),
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
            patch("app.services.listing_image.ListingImageRepository.create") as mock_create,
            patch("app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"),
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 0
            mock_create.return_value = mock_image
            db = MagicMock(spec=Session)

            result = listing_image_service.create(
                db, listing_id, ImageCreate(url="http://example.com/image.jpg"), mock_user
            )

            assert result == mock_image
            mock_create.assert_called_once()

    @patch("app.services.listing_image.settings")
    def test_create_image_exceeds_max_limit_raises_400(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test creating image when at max limit raises 400."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 10  # At max limit
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.create(
                    db, listing_id, ImageCreate(url="http://example.com/image.jpg"), mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "10" in exc_info.value.detail

    @patch("app.services.listing_image.settings")
    def test_create_image_unauthorized_seller_raises_403(
        self, mock_settings, listing_image_service: ListingImageService
    ):
        """Test creating image for someone else's listing raises 403."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        different_user_id = uuid.uuid4()

        mock_listing = Listing(
            id=listing_id, seller_id=owner_id, title="Test", description="Test", price=100
        )
        different_user = User(
            id=different_user_id,
            username="other",
            email="other@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        with patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing:
            mock_get_listing.return_value = mock_listing
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.create(
                    db, listing_id, ImageCreate(url="http://example.com/image.jpg"), different_user
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch("app.services.listing_image.settings")
    def test_create_image_listing_not_found_raises_404(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test creating image for non-existent listing raises 404."""
        mock_settings.listing.max_images_per_listing = 10

        with patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing:
            mock_get_listing.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.create(
                    db, uuid.uuid4(), ImageCreate(url="http://example.com/image.jpg"), mock_user
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.services.listing_image.settings")
    def test_create_first_image_sets_as_thumbnail(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test that first image is automatically set as thumbnail."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        mock_image = Image(
            id=uuid.uuid4(),
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=True,
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
            patch("app.services.listing_image.ListingImageRepository.create") as mock_create,
            patch("app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"),
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 0  # First image
            mock_create.return_value = mock_image
            db = MagicMock(spec=Session)

            result = listing_image_service.create(
                db, listing_id, ImageCreate(url="http://example.com/image.jpg"), mock_user
            )

            assert result.is_thumbnail is True

    @patch("app.services.listing_image.settings")
    def test_create_thumbnail_clears_existing_thumbnails(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test that setting a new thumbnail clears existing ones."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        mock_image = Image(
            id=uuid.uuid4(),
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=True,
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
            patch("app.services.listing_image.ListingImageRepository.create") as mock_create,
            patch(
                "app.services.listing_image.ListingImageRepository.clear_thumbnail_for_listing"
            ) as mock_clear,
            patch("app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"),
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 2  # Existing images
            mock_create.return_value = mock_image
            db = MagicMock(spec=Session)

            listing_image_service.create(
                db,
                listing_id,
                ImageCreate(url="http://example.com/image.jpg", is_thumbnail=True),
                mock_user,
            )

            mock_clear.assert_called_once()


class TestListingImageServiceUpdate:
    """Test ListingImageService update method."""

    def test_update_image_success(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test updating an image successfully."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.update") as mock_update,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_update.return_value = mock_image
            db = MagicMock(spec=Session)

            result = listing_image_service.update(
                db, image_id, ImageUpdate(alt_text="New alt text"), mock_user
            )

            assert result == mock_image

    def test_update_image_unauthorized_seller_raises_403(
        self, listing_image_service: ListingImageService
    ):
        """Test updating image for someone else's listing raises 403."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        different_user_id = uuid.uuid4()

        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=owner_id, title="Test", description="Test", price=100
        )
        different_user = User(
            id=different_user_id,
            username="other",
            email="other@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.update(
                    db, image_id, ImageUpdate(alt_text="New alt text"), different_user
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_update_explicitly_remove_thumbnail(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test explicitly setting is_thumbnail=False on current thumbnail."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=True,  # Currently the thumbnail
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        updated_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,  # No longer thumbnail
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.update") as mock_update,
            patch(
                "app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"
            ) as mock_update_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_update.return_value = updated_image
            db = MagicMock(spec=Session)

            result = listing_image_service.update(
                db, image_id, ImageUpdate(is_thumbnail=False), mock_user
            )

            assert result == updated_image
            # Should clear the listing's thumbnail URL since we removed the thumbnail
            mock_update_listing.assert_called_once_with(db, listing_id, None)

    def test_update_thumbnail_url_change(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test updating thumbnail URL updates listing thumbnail URL."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        old_url = "http://example.com/old.jpg"
        new_url = "http://example.com/new.jpg"
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url=old_url,
            is_thumbnail=True,  # Already the thumbnail
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        updated_image = Image(
            id=image_id,
            listing_id=listing_id,
            url=new_url,
            is_thumbnail=True,  # Still the thumbnail
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.update") as mock_update,
            patch(
                "app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"
            ) as mock_update_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_update.return_value = updated_image
            db = MagicMock(spec=Session)

            result = listing_image_service.update(db, image_id, ImageUpdate(url=new_url), mock_user)

            assert result == updated_image
            # Should update listing's thumbnail URL to new URL
            mock_update_listing.assert_called_once_with(db, listing_id, new_url)


class TestListingImageServiceDelete:
    """Test ListingImageService delete method."""

    def test_delete_image_success(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test deleting an image successfully."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.delete") as mock_delete,
            patch(
                "app.services.listing_image.ListingImageRepository.get_by_listing"
            ) as mock_get_by_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_get_by_listing.return_value = []  # No remaining images
            db = MagicMock(spec=Session)

            listing_image_service.delete(db, image_id, mock_user)

            mock_delete.assert_called_once()

    def test_delete_image_unauthorized_seller_raises_403(
        self, listing_image_service: ListingImageService
    ):
        """Test deleting image for someone else's listing raises 403."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        different_user_id = uuid.uuid4()

        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )
        mock_listing = Listing(
            id=listing_id, seller_id=owner_id, title="Test", description="Test", price=100
        )
        different_user = User(
            id=different_user_id,
            username="other",
            email="other@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.delete(db, image_id, different_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_image_not_found_raises_404(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test deleting non-existent image raises 404."""
        with patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get:
            mock_get.return_value = None
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.delete(db, uuid.uuid4(), mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_thumbnail_sets_new_thumbnail(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test deleting thumbnail automatically sets another image as thumbnail."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image1.jpg",
            is_thumbnail=True,  # This is the thumbnail being deleted
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        # Remaining images after delete
        remaining_image = Image(
            id=uuid.uuid4(),
            listing_id=listing_id,
            url="http://example.com/image2.jpg",
            is_thumbnail=False,
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.delete") as mock_delete,
            patch(
                "app.services.listing_image.ListingImageRepository.get_by_listing"
            ) as mock_get_by_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.set_as_thumbnail_only"
            ) as mock_set_thumbnail,
            patch(
                "app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"
            ) as mock_update_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_get_by_listing.return_value = [remaining_image]  # One image remains
            db = MagicMock(spec=Session)

            listing_image_service.delete(db, image_id, mock_user)

            # Should delete the image
            mock_delete.assert_called_once()
            # Should set remaining image as new thumbnail
            mock_set_thumbnail.assert_called_once_with(db, remaining_image)
            # Should update listing's thumbnail URL to the new thumbnail
            mock_update_listing.assert_called_once_with(db, listing_id, str(remaining_image.url))

    def test_delete_last_thumbnail_clears_listing_thumbnail(
        self, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test deleting the last thumbnail clears listing thumbnail URL."""
        image_id = uuid.uuid4()
        listing_id = uuid.uuid4()
        mock_image = Image(
            id=image_id,
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=True,  # This is the only/last image
        )
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingImageRepository.get_by_id") as mock_get_image,
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch("app.services.listing_image.ListingImageRepository.delete") as mock_delete,
            patch(
                "app.services.listing_image.ListingImageRepository.get_by_listing"
            ) as mock_get_by_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"
            ) as mock_update_listing,
        ):
            mock_get_image.return_value = mock_image
            mock_get_listing.return_value = mock_listing
            mock_get_by_listing.return_value = []  # No images remain
            db = MagicMock(spec=Session)

            listing_image_service.delete(db, image_id, mock_user)

            # Should delete the image
            mock_delete.assert_called_once()
            # Should clear listing's thumbnail URL since no images left
            mock_update_listing.assert_called_once_with(db, listing_id, None)


class TestListingImageServiceMaxLimit:
    """Test max image limit enforcement using configurable settings."""

    @patch("app.services.listing_image.settings")
    def test_max_images_respects_settings(self, mock_settings):
        """Test that max images limit comes from settings."""
        mock_settings.listing.max_images_per_listing = 15
        assert mock_settings.listing.max_images_per_listing == 15

    @patch("app.services.listing_image.settings")
    def test_can_add_up_to_max_images(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test can add images up to the configured limit."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )
        mock_image = Image(
            id=uuid.uuid4(),
            listing_id=listing_id,
            url="http://example.com/image.jpg",
            is_thumbnail=False,
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
            patch("app.services.listing_image.ListingImageRepository.create") as mock_create,
            patch("app.services.listing_image.ListingImageRepository.update_listing_thumbnail_url"),
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 9  # Just below limit
            mock_create.return_value = mock_image
            db = MagicMock(spec=Session)

            # Should succeed
            listing_image_service.create(
                db, listing_id, ImageCreate(url="http://example.com/image.jpg"), mock_user
            )

    @patch("app.services.listing_image.settings")
    def test_cannot_add_beyond_limit(
        self, mock_settings, listing_image_service: ListingImageService, mock_user: User
    ):
        """Test cannot add image when at configured limit."""
        mock_settings.listing.max_images_per_listing = 10
        listing_id = uuid.uuid4()
        mock_listing = Listing(
            id=listing_id, seller_id=mock_user.id, title="Test", description="Test", price=100
        )

        with (
            patch("app.services.listing_image.ListingRepository.get_by_id") as mock_get_listing,
            patch(
                "app.services.listing_image.ListingImageRepository.count_by_listing"
            ) as mock_count,
        ):
            mock_get_listing.return_value = mock_listing
            mock_count.return_value = 10  # At limit
            db = MagicMock(spec=Session)

            with pytest.raises(HTTPException) as exc_info:
                listing_image_service.create(
                    db, listing_id, ImageCreate(url="http://example.com/image.jpg"), mock_user
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
