"""
Test listing image endpoints.

Tests for listing image CRUD operations and thumbnail management.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.listing import Listing
from app.models.listing_image import Image


class TestUpdateImage:
    """Test PATCH /listings/{listing_id}/images/{image_id} endpoint."""

    def test_update_image_url(
        self, authenticated_client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test updating image URL."""
        update_data = {"url": "https://example.com/new-image.jpg"}
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}/images/{test_image.id}", json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["url"] == update_data["url"]

        # Verify the update persisted via the listing
        listing_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        listing_data = listing_response.json()
        updated_image = next(
            img for img in listing_data["images"] if img["id"] == str(test_image.id)
        )
        assert updated_image["url"] == update_data["url"]

    def test_update_image_alt_text(
        self, authenticated_client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test updating image alt text."""
        update_data = {"alt_text": "New description"}
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}/images/{test_image.id}", json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["alt_text"] == update_data["alt_text"]

        # Verify the update persisted via the listing
        listing_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        listing_data = listing_response.json()
        updated_image = next(
            img for img in listing_data["images"] if img["id"] == str(test_image.id)
        )
        assert updated_image["alt_text"] == update_data["alt_text"]

    def test_update_image_set_thumbnail(
        self, authenticated_client: TestClient, test_listing: Listing, test_images: list[Image]
    ):
        """Test setting an image as thumbnail."""
        non_thumbnail_image = [img for img in test_images if not img.is_thumbnail][0]
        update_data = {"is_thumbnail": True}
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}/images/{non_thumbnail_image.id}",
            json=update_data,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_thumbnail"] is True

        # Verify thumbnail update persisted by checking listing
        listing_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        listing_data = listing_response.json()
        # Verify this image is now the thumbnail
        updated_image = next(
            img for img in listing_data["images"] if img["id"] == str(non_thumbnail_image.id)
        )
        assert updated_image["is_thumbnail"] is True
        # Verify listing's thumbnail_url points to this image
        assert listing_data["thumbnail_url"] == str(non_thumbnail_image.url)

    def test_update_image_not_owner(
        self,
        authenticated_client: TestClient,
        other_user_listing: Listing,
        db_session,
    ):
        """Test updating someone else's image fails."""
        # Create image for other user's listing
        image = Image(
            id=uuid.uuid4(),
            listing_id=other_user_listing.id,
            url="https://example.com/image.jpg",
            is_thumbnail=True,
        )
        db_session.add(image)
        db_session.commit()

        response = authenticated_client.patch(
            f"/api/v1/listings/{other_user_listing.id}/images/{image.id}",
            json={"alt_text": "Hacked"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_image_without_auth(
        self, client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test updating image without authentication fails."""
        response = client.patch(
            f"/api/v1/listings/{test_listing.id}/images/{test_image.id}",
            json={"alt_text": "New"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_image_no_fields(
        self, authenticated_client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test updating image with no fields returns unchanged image."""
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}/images/{test_image.id}", json={}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Image should be unchanged
        assert data["id"] == str(test_image.id)
        assert data["url"] == str(test_image.url)


class TestDeleteImage:
    """Test DELETE /listings/{listing_id}/images/{image_id} endpoint."""

    def test_delete_image_success(
        self, authenticated_client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test deleting an image."""
        response = authenticated_client.delete(
            f"/api/v1/listings/{test_listing.id}/images/{test_image.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify image is removed from listing
        listing_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        listing_data = listing_response.json()
        image_ids = [img["id"] for img in listing_data["images"]]
        assert str(test_image.id) not in image_ids

    def test_delete_thumbnail_sets_new_thumbnail(
        self, authenticated_client: TestClient, test_listing: Listing, test_images: list[Image]
    ):
        """Test deleting thumbnail automatically sets a new one."""
        thumbnail_image = [img for img in test_images if img.is_thumbnail][0]
        response = authenticated_client.delete(
            f"/api/v1/listings/{test_listing.id}/images/{thumbnail_image.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify another image became thumbnail by checking the listing
        get_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        listing_data = get_response.json()
        # If there are remaining images, one should be the thumbnail
        if len(test_images) > 1:
            assert listing_data["thumbnail_url"] is not None
            # Check that the thumbnail_url is one of the remaining images
            remaining_images = [img for img in test_images if img.id != thumbnail_image.id]
            assert any(str(img.url) == listing_data["thumbnail_url"] for img in remaining_images)

    def test_delete_image_not_owner(
        self,
        authenticated_client: TestClient,
        other_user_listing: Listing,
        db_session,
    ):
        """Test deleting someone else's image fails."""
        image = Image(
            id=uuid.uuid4(),
            listing_id=other_user_listing.id,
            url="https://example.com/image.jpg",
            is_thumbnail=True,
        )
        db_session.add(image)
        db_session.commit()

        response = authenticated_client.delete(
            f"/api/v1/listings/{other_user_listing.id}/images/{image.id}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_image_without_auth(
        self, client: TestClient, test_listing: Listing, test_image: Image
    ):
        """Test deleting image without authentication fails."""
        response = client.delete(f"/api/v1/listings/{test_listing.id}/images/{test_image.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
