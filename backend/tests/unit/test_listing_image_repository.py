"""
Unit tests for ListingImageRepository.

Tests the data access layer for listing image operations.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.enums import Category, Condition
from app.models.listing import Listing
from app.models.listing_image import Image
from app.models.user import User
from app.repository.listing_image import ListingImageRepository
from app.schemas.listing_image import ImageCreate, ImageUpdate


@pytest.fixture
def test_listing(db_session: Session, test_user: User) -> Listing:
    """Create a test listing for image tests."""
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
def test_image(db_session: Session, test_listing: Listing) -> Image:
    """Create a test image."""
    image = Image(
        listing_id=test_listing.id,
        url="https://example.com/image1.jpg",
        is_thumbnail=False,
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


class TestListingImageRepositoryGet:
    """Test ListingImageRepository get methods."""

    def test_get_by_id_found(self, db_session: Session, test_image: Image):
        """Test getting image by ID when exists."""
        result = ListingImageRepository.get_by_id(db_session, test_image.id)

        assert result is not None
        assert result.id == test_image.id
        assert result.url == test_image.url

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting image by ID when doesn't exist."""
        random_id = uuid.uuid4()
        result = ListingImageRepository.get_by_id(db_session, random_id)

        assert result is None

    def test_get_by_listing(self, db_session: Session, test_listing: Listing, test_image: Image):
        """Test getting all images for a listing."""
        results = ListingImageRepository.get_by_listing(db_session, test_listing.id)

        assert len(results) == 1
        assert results[0].id == test_image.id
        assert results[0].listing_id == test_listing.id

    def test_get_by_listing_multiple_images(self, db_session: Session, test_listing: Listing):
        """Test getting multiple images for a listing."""
        image1 = Image(listing_id=test_listing.id, url="https://example.com/1.jpg")
        image2 = Image(listing_id=test_listing.id, url="https://example.com/2.jpg")
        db_session.add_all([image1, image2])
        db_session.commit()

        results = ListingImageRepository.get_by_listing(db_session, test_listing.id)

        assert len(results) == 2
        urls = {img.url for img in results}
        assert "https://example.com/1.jpg" in urls
        assert "https://example.com/2.jpg" in urls

    def test_get_thumbnail(self, db_session: Session, test_listing: Listing):
        """Test getting thumbnail image for a listing."""
        thumbnail = Image(
            listing_id=test_listing.id,
            url="https://example.com/thumbnail.jpg",
            is_thumbnail=True,
        )
        db_session.add(thumbnail)
        db_session.commit()

        result = ListingImageRepository.get_thumbnail(db_session, test_listing.id)

        assert result is not None
        assert result.is_thumbnail is True
        assert result.url == "https://example.com/thumbnail.jpg"

    def test_get_thumbnail_not_found(self, db_session: Session, test_listing: Listing):
        """Test getting thumbnail when none exists."""
        result = ListingImageRepository.get_thumbnail(db_session, test_listing.id)

        assert result is None

    def test_count_by_listing(self, db_session: Session, test_listing: Listing, test_image: Image):
        """Test counting images for a listing."""
        count = ListingImageRepository.count_by_listing(db_session, test_listing.id)

        assert count == 1

    def test_count_by_listing_multiple(self, db_session: Session, test_listing: Listing):
        """Test counting multiple images."""
        image1 = Image(listing_id=test_listing.id, url="https://example.com/1.jpg")
        image2 = Image(listing_id=test_listing.id, url="https://example.com/2.jpg")
        db_session.add_all([image1, image2])
        db_session.commit()

        count = ListingImageRepository.count_by_listing(db_session, test_listing.id)

        assert count == 2


class TestListingImageRepositoryCreate:
    """Test ListingImageRepository create method."""

    def test_create_image_success(self, db_session: Session, test_listing: Listing):
        """Test creating an image."""
        result = ListingImageRepository.create(
            db_session,
            test_listing.id,
            url="https://example.com/new.jpg",
            is_thumbnail=False,
            alt_text=None,
        )

        assert result.id is not None
        assert result.listing_id == test_listing.id
        assert result.url == "https://example.com/new.jpg"
        assert result.is_thumbnail is False

    def test_create_image_as_thumbnail(self, db_session: Session, test_listing: Listing):
        """Test creating image as thumbnail."""
        result = ListingImageRepository.create(
            db_session,
            test_listing.id,
            url="https://example.com/thumb.jpg",
            is_thumbnail=True,
            alt_text=None,
        )

        assert result.is_thumbnail is True

    def test_create_image_with_alt_text(self, db_session: Session, test_listing: Listing):
        """Test creating image with alt text."""
        result = ListingImageRepository.create(
            db_session,
            test_listing.id,
            url="https://example.com/alt.jpg",
            is_thumbnail=False,
            alt_text="Test alt text",
        )

        assert result.alt_text == "Test alt text"


class TestListingImageRepositoryUpdate:
    """Test ListingImageRepository update method."""

    def test_update_image_url(self, db_session: Session, test_image: Image):
        """Test updating image URL."""
        result = ListingImageRepository.update(
            db_session,
            test_image,
            url="https://example.com/updated.jpg",
            is_thumbnail=test_image.is_thumbnail,
            alt_text=test_image.alt_text,
        )

        assert result.url == "https://example.com/updated.jpg"
        assert result.id == test_image.id

    def test_update_image_alt_text(self, db_session: Session, test_image: Image):
        """Test updating image alt text."""
        result = ListingImageRepository.update(
            db_session,
            test_image,
            url=test_image.url,
            is_thumbnail=test_image.is_thumbnail,
            alt_text="Updated alt text",
        )

        assert result.alt_text == "Updated alt text"

    def test_update_image_thumbnail_status(self, db_session: Session, test_image: Image):
        """Test updating image thumbnail status."""
        result = ListingImageRepository.update(
            db_session,
            test_image,
            url=test_image.url,
            is_thumbnail=True,
            alt_text=test_image.alt_text,
        )

        assert result.is_thumbnail is True

    def test_update_image_multiple_fields(self, db_session: Session, test_image: Image):
        """Test updating multiple image fields."""
        result = ListingImageRepository.update(
            db_session,
            test_image,
            url="https://example.com/multi.jpg",
            is_thumbnail=True,
            alt_text="Multi update",
        )

        assert result.url == "https://example.com/multi.jpg"
        assert result.alt_text == "Multi update"
        assert result.is_thumbnail is True


class TestListingImageRepositoryThumbnail:
    """Test thumbnail-specific functionality."""

    def test_set_as_thumbnail_only(self, db_session: Session, test_listing: Listing):
        """Test setting image as thumbnail when no others exist."""
        # Create a single image (no existing thumbnails)
        img = Image(listing_id=test_listing.id, url="https://example.com/1.jpg", is_thumbnail=False)
        db_session.add(img)
        db_session.commit()

        # Set as the only thumbnail
        result = ListingImageRepository.set_as_thumbnail_only(db_session, img)

        assert result.is_thumbnail is True
        # Verify it's set
        db_session.refresh(img)
        assert img.is_thumbnail is True

    def test_clear_thumbnail_for_listing(self, db_session: Session, test_listing: Listing):
        """Test clearing all thumbnails for a listing."""
        img1 = Image(listing_id=test_listing.id, url="https://example.com/1.jpg", is_thumbnail=True)
        img2 = Image(listing_id=test_listing.id, url="https://example.com/2.jpg", is_thumbnail=True)
        db_session.add_all([img1, img2])
        db_session.commit()

        ListingImageRepository.clear_thumbnail_for_listing(db_session, test_listing.id)

        # Verify all images are no longer thumbnails
        images = ListingImageRepository.get_by_listing(db_session, test_listing.id)
        assert all(not img.is_thumbnail for img in images)

    def test_update_listing_thumbnail_url(self, db_session: Session, test_listing: Listing):
        """Test updating listing's thumbnail_url field."""
        # Create thumbnail image
        thumbnail = Image(
            listing_id=test_listing.id,
            url="https://example.com/thumb.jpg",
            is_thumbnail=True,
        )
        db_session.add(thumbnail)
        db_session.commit()

        # Update listing's thumbnail_url
        ListingImageRepository.update_listing_thumbnail_url(
            db_session, test_listing.id, "https://example.com/thumb.jpg"
        )

        db_session.refresh(test_listing)
        assert test_listing.thumbnail_url == "https://example.com/thumb.jpg"


class TestListingImageRepositoryDelete:
    """Test ListingImageRepository delete methods."""

    def test_delete_image(self, db_session: Session, test_image: Image):
        """Test deleting a single image."""
        image_id = test_image.id

        ListingImageRepository.delete(db_session, test_image)

        # Verify image is deleted
        deleted_image = ListingImageRepository.get_by_id(db_session, image_id)
        assert deleted_image is None

    def test_delete_image_removes_from_session(self, db_session: Session, test_image: Image):
        """Test that deleted image is removed from session."""
        ListingImageRepository.delete(db_session, test_image)

        assert test_image not in db_session

    def test_delete_all_for_listing(self, db_session: Session, test_listing: Listing):
        """Test deleting all images for a listing."""
        # Create multiple images
        img1 = Image(listing_id=test_listing.id, url="https://example.com/1.jpg")
        img2 = Image(listing_id=test_listing.id, url="https://example.com/2.jpg")
        db_session.add_all([img1, img2])
        db_session.commit()

        ListingImageRepository.delete_all_for_listing(db_session, test_listing.id)

        # Verify all images are deleted
        images = ListingImageRepository.get_by_listing(db_session, test_listing.id)
        assert len(images) == 0

    def test_delete_all_for_listing_empty(self, db_session: Session, test_listing: Listing):
        """Test deleting all images when none exist."""
        # Should not raise error
        ListingImageRepository.delete_all_for_listing(db_session, test_listing.id)

        images = ListingImageRepository.get_by_listing(db_session, test_listing.id)
        assert len(images) == 0


class TestListingImageRepositoryUpdateThumbnail:
    """Test ListingImageRepository update_listing_thumbnail_url method."""

    def test_update_listing_thumbnail_url_listing_not_found(self, db_session: Session):
        """Test update_listing_thumbnail_url raises ValueError when listing not found."""
        nonexistent_listing_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Cannot update thumbnail_url"):
            ListingImageRepository.update_listing_thumbnail_url(
                db_session, nonexistent_listing_id, "https://example.com/thumb.jpg"
            )
