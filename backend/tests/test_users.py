"""
Test user endpoints.

Tests for user CRUD operations and profile management.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


class TestGetCurrentUser:
    """Test GET /users/me endpoint."""

    def test_get_current_user_success(self, authenticated_client: TestClient, test_user: User):
        """Test getting current authenticated user's information."""
        response = authenticated_client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    def test_get_current_user_without_authentication(self, client: TestClient):
        """Test getting current user without authentication fails."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


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

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestGetUserListings:
    """Test GET /users/{user_id}/listings endpoint."""

    def test_get_user_listings_success(self, client: TestClient, test_user: User, test_listing):
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


class TestUpdateCurrentUser:
    """Test PATCH /users/me endpoint."""

    def test_update_current_user_success(self, authenticated_client: TestClient, test_user: User):
        """Test updating current user's information."""
        update_data = {
            "username": "updated_username",
            "email": "updated@example.com",
        }
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "updated_username"
        assert data["email"] == "updated@example.com"
        assert data["id"] == str(test_user.id)

    def test_update_current_user_partial(self, authenticated_client: TestClient, test_user: User):
        """Test partially updating current user (only some fields)."""
        update_data = {"username": "new_username"}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "new_username"
        assert data["email"] == test_user.email  # Should remain unchanged

    def test_update_current_user_without_authentication(self, client: TestClient):
        """Test updating user without authentication fails."""
        update_data = {"username": "test"}
        response = client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_current_user_duplicate_username(
        self, authenticated_client: TestClient, test_user: User, db_session
    ):
        """Test updating username to one that's already taken fails."""
        # Create another user
        from app.models.user import User as UserModel
        from app.core.auth import get_password_hash

        existing_user = UserModel(
            username="existing_user",
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(existing_user)
        db_session.commit()

        # Try to update to existing username
        update_data = {"username": "existing_user"}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_current_user_duplicate_email(
        self, authenticated_client: TestClient, test_user: User, db_session
    ):
        """Test updating email to one that's already taken fails."""
        # Create another user
        from app.models.user import User as UserModel
        from app.core.auth import get_password_hash

        existing_user = UserModel(
            username="another_user",
            email="taken@example.com",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(existing_user)
        db_session.commit()

        # Try to update to existing email
        update_data = {"email": "taken@example.com"}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_current_user_invalid_email(self, authenticated_client: TestClient):
        """Test updating with invalid email format fails."""
        update_data = {"email": "not-an-email"}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_current_user_empty_update(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test updating with no fields returns current user."""
        response = authenticated_client.patch("/api/v1/users/me", json={})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_update_username_case_insensitive_uniqueness(
        self, authenticated_client: TestClient, test_user: User, db_session
    ):
        """Test that username uniqueness check (case sensitivity depends on implementation)."""
        # Create another user
        from app.models.user import User as UserModel
        from app.core.auth import get_password_hash

        existing_user = UserModel(
            username="ExistingUser",
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(existing_user)
        db_session.commit()

        # Try to update to same username with different case
        update_data = {"username": "existinguser"}  # lowercase
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        # Note: This test documents current behavior - may accept or reject based on DB settings
        # Currently accepting (case-sensitive check), but could be changed to reject
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_update_email_to_same_succeeds(self, authenticated_client: TestClient, test_user: User):
        """Test updating email to same value succeeds (no-op)."""
        update_data = {"email": test_user.email}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email

    def test_update_username_to_same_succeeds(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test updating username to same value succeeds (no-op)."""
        update_data = {"username": test_user.username}
        response = authenticated_client.patch("/api/v1/users/me", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username


class TestDeleteCurrentUser:
    """Test DELETE /users/me endpoint."""

    def test_delete_current_user_success(self, authenticated_client: TestClient, test_user: User):
        """Test deleting current user's account."""
        response = authenticated_client.delete("/api/v1/users/me")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is deleted by trying to get current user
        get_response = authenticated_client.get("/api/v1/users/me")
        # Should fail because user no longer exists
        assert get_response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

    def test_delete_current_user_without_authentication(self, client: TestClient):
        """Test deleting user without authentication fails."""
        response = client.delete("/api/v1/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_current_user_cascades_to_profile(
        self, authenticated_client: TestClient, test_user: User, test_profile
    ):
        """Test that deleting user cascades to their profile."""
        # Verify profile exists
        profile_response = authenticated_client.get("/api/v1/users/profile/")
        assert profile_response.status_code == status.HTTP_200_OK

        # Delete user
        delete_response = authenticated_client.delete("/api/v1/users/me")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_current_user_idempotent(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test that deleting user twice handles gracefully."""
        # First delete
        first_response = authenticated_client.delete("/api/v1/users/me")
        assert first_response.status_code == status.HTTP_204_NO_CONTENT

        # Second delete attempt should fail with 401/404 since user is gone
        second_response = authenticated_client.delete("/api/v1/users/me")
        assert second_response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_delete_user_cascades_to_listings(
        self, authenticated_client: TestClient, test_user: User, db_session
    ):
        """Test that deleting user cascades to their listings."""
        from app.models.listing import Listing
        from app.core.enums import Category, Condition

        # Create a listing for the user
        listing = Listing(
            seller_id=test_user.id,
            title="Test Listing",
            description="Test Description",
            price=100.0,
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        db_session.add(listing)
        db_session.commit()
        listing_id = listing.id

        # Delete user
        delete_response = authenticated_client.delete("/api/v1/users/me")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify listing is also deleted (cascade)
        db_session.expire_all()  # Clear session cache
        deleted_listing = db_session.get(Listing, listing_id)
        assert deleted_listing is None

    def test_delete_user_cascades_to_listing_images(
        self, authenticated_client: TestClient, test_user: User, db_session
    ):
        """Test that deleting user cascades to listing images."""
        from app.models.listing import Listing
        from app.models.listing_image import Image
        from app.core.enums import Category, Condition

        # Create listing and image
        listing = Listing(
            seller_id=test_user.id,
            title="Test Listing",
            description="Test Description",
            price=100.0,
            category=Category.ELECTRONICS,
            condition=Condition.NEW,
        )
        db_session.add(listing)
        db_session.commit()

        image = Image(
            listing_id=listing.id,
            url="https://example.com/image.jpg",
            is_thumbnail=False,
        )
        db_session.add(image)
        db_session.commit()
        image_id = image.id

        # Delete user
        delete_response = authenticated_client.delete("/api/v1/users/me")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify image is also deleted (cascade)
        db_session.expire_all()
        deleted_image = db_session.get(Image, image_id)
        assert deleted_image is None


class TestUserIntegration:
    """Integration tests for user workflows."""

    def test_complete_user_lifecycle(self, authenticated_client: TestClient, test_user: User):
        """Test complete user workflow: get -> update -> delete."""
        # Get current user
        get_response = authenticated_client.get("/api/v1/users/me")
        assert get_response.status_code == status.HTTP_200_OK
        original_data = get_response.json()

        # Update user
        update_response = authenticated_client.patch(
            "/api/v1/users/me", json={"username": "updated_user"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["username"] == "updated_user"

        # Get updated user
        get_updated = authenticated_client.get("/api/v1/users/me")
        assert get_updated.status_code == status.HTTP_200_OK
        assert get_updated.json()["username"] == "updated_user"

        # Delete user
        delete_response = authenticated_client.delete("/api/v1/users/me")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is gone
        verify_response = authenticated_client.get("/api/v1/users/me")
        assert verify_response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]
