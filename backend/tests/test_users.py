"""
Test user endpoints.

Tests for user CRUD operations and profile management.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


class TestGetUser:
    """Test GET /users/{user_id} endpoint."""

    def test_get_user_success(self, client: TestClient, test_user: User):
        """Test getting user by ID."""
        response = client.get(f"/api/v1/users/{test_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    def test_get_user_not_found(self, client: TestClient):
        """Test getting non-existent user returns 404."""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/users/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_invalid_uuid(self, client: TestClient):
        """Test getting user with invalid UUID format."""
        response = client.get("/api/v1/users/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetUserListings:
    """Test GET /users/{user_id}/listings endpoint."""

    def test_get_user_listings_success(
        self, client: TestClient, test_user: User, test_listing
    ):
        """Test getting listings for a user."""
        response = client.get(f"/api/v1/users/{test_user.id}/listings")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert data["count"] >= 1
        assert data["items"][0]["seller_id"] == str(test_user.id)

    def test_get_user_listings_empty(self, client: TestClient, test_user: User):
        """Test getting listings for user with no listings."""
        response = client.get(f"/api/v1/users/{test_user.id}/listings")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert data["count"] == 0

    def test_get_user_listings_with_pagination(
        self, client: TestClient, test_user: User, test_listing
    ):
        """Test getting user listings with pagination parameters."""
        response = client.get(f"/api/v1/users/{test_user.id}/listings?limit=5&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
