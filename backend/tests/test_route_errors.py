"""
Test route error handling.

Tests for various error scenarios across all routes including:
- Invalid UUIDs
- Malformed request bodies
- Missing required fields
- Type validation errors
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.listing import Listing
from app.models.user import User


class TestInvalidUUIDs:
    """Test routes with invalid UUID parameters."""

    def test_get_listing_invalid_uuid(self, client: TestClient):
        """Test getting listing with invalid UUID format."""
        response = client.get("/api/v1/listings/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_get_user_invalid_uuid(self, client: TestClient):
        """Test getting user with invalid UUID format."""
        response = client.get("/api/v1/users/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_listing_invalid_uuid(self, authenticated_client: TestClient):
        """Test updating listing with invalid UUID."""
        response = authenticated_client.patch(
            "/api/v1/listings/not-a-uuid",
            json={"title": "Updated"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_delete_listing_invalid_uuid(self, authenticated_client: TestClient):
        """Test deleting listing with invalid UUID."""
        response = authenticated_client.delete("/api/v1/listings/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_image_invalid_listing_uuid(self, authenticated_client: TestClient):
        """Test creating image with invalid listing UUID."""
        response = authenticated_client.post(
            "/api/v1/listings/not-a-uuid/images",
            json={"url": "http://example.com/image.jpg"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_admin_get_action_invalid_uuid(self, admin_client: TestClient):
        """Test getting admin action with invalid UUID."""
        response = admin_client.get("/api/v1/admin/actions/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_admin_delete_action_invalid_uuid(self, admin_client: TestClient):
        """Test deleting admin action with invalid UUID."""
        response = admin_client.delete("/api/v1/admin/actions/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_admin_strike_user_invalid_uuid(self, admin_client: TestClient):
        """Test striking user with invalid UUID."""
        response = admin_client.post(
            "/api/v1/admin/users/not-a-uuid/strike",
            json={"reason": "Test"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_admin_ban_user_invalid_uuid(self, admin_client: TestClient):
        """Test banning user with invalid UUID."""
        response = admin_client.post(
            "/api/v1/admin/users/not-a-uuid/ban",
            json={"reason": "Test"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_admin_remove_listing_invalid_uuid(self, admin_client: TestClient):
        """Test removing listing with invalid UUID."""
        response = admin_client.post(
            "/api/v1/admin/listings/not-a-uuid/remove",
            json={"reason": "Test"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestMissingRequiredFields:
    """Test routes with missing required fields."""

    def test_create_listing_missing_title(self, authenticated_client: TestClient):
        """Test creating listing without title."""
        response = authenticated_client.post(
            "/api/v1/listings",
            json={
                "description": "Test description",
                "price": 100.0,
                "category": "electronics",
                "condition": "new",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_listing_missing_price(self, authenticated_client: TestClient):
        """Test creating listing without price."""
        response = authenticated_client.post(
            "/api/v1/listings",
            json={
                "title": "Test Listing",
                "description": "Test description",
                "category": "electronics",
                "condition": "new",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_image_missing_url(
        self, authenticated_client: TestClient, test_listing: Listing
    ):
        """Test creating image without URL."""
        response = authenticated_client.post(
            f"/api/v1/listings/{test_listing.id}/images",
            json={"is_thumbnail": False},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser"},  # Missing password
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestInvalidDataTypes:
    """Test routes with invalid data types."""

    def test_create_listing_price_as_string(self, authenticated_client: TestClient):
        """Test creating listing with price as invalid string."""
        response = authenticated_client.post(
            "/api/v1/listings",
            json={
                "title": "Test Listing",
                "description": "Test description",
                "price": "not-a-number",
                "category": "electronics",
                "condition": "new",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_image_invalid_url_format(
        self, authenticated_client: TestClient, test_listing: Listing
    ):
        """Test creating image with invalid URL format."""
        response = authenticated_client.post(
            f"/api/v1/listings/{test_listing.id}/images",
            json={"url": "not-a-valid-url"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_listing_invalid_boolean(
        self, authenticated_client: TestClient, test_listing: Listing
    ):
        """Test updating listing with invalid boolean value."""
        response = authenticated_client.patch(
            f"/api/v1/listings/{test_listing.id}",
            json={"is_active": "not-a-boolean"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestEmptyRequestBodies:
    """Test routes with empty or null request bodies."""

    def test_create_listing_empty_body(self, authenticated_client: TestClient):
        """Test creating listing with empty body."""
        response = authenticated_client.post("/api/v1/listings", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestQueryParameterValidation:
    """Test route query parameter validation."""

    def test_get_listings_invalid_limit(self, client: TestClient):
        """Test getting listings with invalid limit value."""
        response = client.get("/api/v1/listings?limit=not-a-number")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
