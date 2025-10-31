"""
Test listing endpoints.

Tests for listing CRUD operations, filtering, and pagination.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.listing import Listing
from app.models.user import User


class TestCreateListing:
    """Test POST /listings endpoint."""

    def test_create_listing_success(
        self, authenticated_client: TestClient, test_user: User, valid_listing_data: dict
    ):
        """Test creating a new listing."""
        response = authenticated_client.post("/api/v1/listings", json=valid_listing_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == valid_listing_data["title"]
        assert data["price"] == str(valid_listing_data["price"])
        assert data["seller_id"] == str(test_user.id)
        assert "id" in data
        assert data["is_active"] is True

    def test_create_listing_without_auth(self, client: TestClient, valid_listing_data: dict):
        """Test creating listing without authentication fails."""
        response = client.post("/api/v1/listings", json=valid_listing_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_listing_invalid_condition(
        self, authenticated_client: TestClient, valid_listing_data: dict
    ):
        """Test creating listing with invalid condition fails."""
        valid_listing_data["condition"] = "invalid_condition"
        response = authenticated_client.post("/api/v1/listings", json=valid_listing_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_listing_negative_price(
        self, authenticated_client: TestClient, valid_listing_data: dict
    ):
        """Test creating listing with negative price fails."""
        valid_listing_data["price"] = -10.00
        response = authenticated_client.post("/api/v1/listings", json=valid_listing_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_listing_missing_required_fields(self, authenticated_client: TestClient):
        """Test creating listing with missing fields fails."""
        response = authenticated_client.post("/api/v1/listings", json={"title": "Test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetListings:
    """Test GET /listings endpoint."""

    def test_get_all_listings(self, client: TestClient, test_listing: Listing):
        """Test getting all listings."""
        response = client.get("/api/v1/listings")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
        assert data["count"] >= 1

    def test_get_listings_pagination(self, client: TestClient, test_listing: Listing):
        """Test listing pagination."""
        response = client.get("/api/v1/listings?limit=5&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 5

    def test_get_listings_filter_by_category(self, client: TestClient, test_listing: Listing):
        """Test filtering listings by category."""
        response = client.get(f"/api/v1/listings?category={test_listing.category.value}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["category"] == test_listing.category.value for item in data["items"])

    def test_get_listings_filter_by_condition(self, client: TestClient, test_listing: Listing):
        """Test filtering listings by condition."""
        response = client.get(f"/api/v1/listings?condition={test_listing.condition.value}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["condition"] == test_listing.condition.value for item in data["items"])

    def test_get_listings_filter_by_price_range(self, client: TestClient, test_listing: Listing):
        """Test filtering listings by price range."""
        response = client.get("/api/v1/listings?min_price=0&max_price=1000")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(0 <= float(item["price"]) <= 1000 for item in data["items"])

    def test_get_listings_search_query(self, client: TestClient, test_listing: Listing):
        """Test searching listings by query."""
        response = client.get(f"/api/v1/listings?search={test_listing.title[:5]}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] >= 1


class TestGetListing:
    """Test GET /listings/{listing_id} endpoint."""

    def test_get_listing_success(self, client: TestClient, test_listing: Listing):
        """Test getting a single listing by ID."""
        response = client.get(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_listing.id)
        assert data["title"] == test_listing.title
        assert data["price"] == str(test_listing.price)
        assert "images" in data
        assert isinstance(data["images"], list)

    def test_get_listing_with_images(self, client: TestClient, test_listing: Listing, test_images):
        """Test getting a listing includes all its images."""
        response = client.get(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "images" in data
        assert len(data["images"]) == len(test_images)
        # Verify images are ordered by created_at
        for i in range(len(data["images"]) - 1):
            assert data["images"][i]["created_at"] <= data["images"][i + 1]["created_at"]
        # Verify one image is the thumbnail
        thumbnails = [img for img in data["images"] if img["is_thumbnail"]]
        assert len(thumbnails) == 1

    def test_get_listing_not_found(self, client: TestClient):
        """Test getting non-existent listing returns 404."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/listings/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_listing_invalid_uuid(self, client: TestClient):
        """Test getting listing with invalid UUID format."""
        response = client.get("/api/v1/listings/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestUpdateListing:
    """Test PATCH /listings/{listing_id} endpoint."""

    def test_update_listing_success(self, authenticated_client: TestClient, test_listing: Listing):
        """Test updating own listing."""
        update_data = {"title": "Updated Title", "price": 600.00}
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}", json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["price"] == "600.00"

    def test_update_listing_partial(self, authenticated_client: TestClient, test_listing: Listing):
        """Test partial update of listing."""
        update_data = {"price": 550.00}
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}", json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["price"] == "550.00"
        assert data["title"] == test_listing.title  # Unchanged

    def test_update_listing_not_owner(
        self, authenticated_client: TestClient, other_user_listing: Listing
    ):
        """Test updating someone else's listing fails."""
        update_data = {"title": "Hacked Title"}
        response = authenticated_client.patch(
            f"/api/v1/listings/{other_user_listing.id}", json=update_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_listing_without_auth(self, client: TestClient, test_listing: Listing):
        """Test updating listing without authentication fails."""
        response = client.patch(f"/api/v1/listings/{test_listing.id}", json={"title": "New"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_listing_not_found(self, authenticated_client: TestClient):
        """Test updating non-existent listing returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_client.patch(f"/api/v1/listings/{fake_id}", json={"title": "New"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_listing_deactivate(
        self, authenticated_client: TestClient, test_listing: Listing
    ):
        """Test deactivating a listing."""
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}", json={"is_active": False}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False


class TestDeleteListing:
    """Test DELETE /listings/{listing_id} endpoint."""

    def test_delete_listing_success(self, authenticated_client: TestClient, test_listing: Listing):
        """Test deleting own listing."""
        response = authenticated_client.delete(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify listing is deleted
        get_response = authenticated_client.get(f"/api/v1/listings/{test_listing.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_listing_not_owner(
        self, authenticated_client: TestClient, other_user_listing: Listing
    ):
        """Test deleting someone else's listing fails."""
        response = authenticated_client.delete(f"/api/v1/listings/{other_user_listing.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_listing_without_auth(self, client: TestClient, test_listing: Listing):
        """Test deleting listing without authentication fails."""
        response = client.delete(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_listing_not_found(self, authenticated_client: TestClient):
        """Test deleting non-existent listing returns 404."""
        fake_id = uuid.uuid4()
        response = authenticated_client.delete(f"/api/v1/listings/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
