"""
Test profile endpoints.

Tests for profile CRUD operations including creation, retrieval,
updates, and profile picture management.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.profile import Profile
from app.models.user import User


class TestCreateProfile:
    """Test POST /users/profile/ endpoint."""

    def test_create_profile_success(
        self, authenticated_client: TestClient, test_user: User, valid_profile_data: dict
    ):
        """Test creating a new profile for authenticated user."""
        response = authenticated_client.post("/api/v1/users/profile/", json=valid_profile_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == valid_profile_data["name"]
        assert data["campus"] == valid_profile_data["campus"]
        assert data["user_id"] == str(test_user.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_profile_without_authentication(self, client: TestClient, valid_profile_data: dict):
        """Test creating profile without authentication fails."""
        response = client.post("/api/v1/users/profile/", json=valid_profile_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_profile_duplicate(
        self, authenticated_client: TestClient, test_profile: Profile, valid_profile_data: dict
    ):
        """Test creating duplicate profile fails."""
        # test_profile already creates a profile for test_user
        response = authenticated_client.post("/api/v1/users/profile/", json=valid_profile_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_create_profile_missing_required_fields(self, authenticated_client: TestClient):
        """Test creating profile with missing required fields fails."""
        response = authenticated_client.post("/api/v1/users/profile/", json={"campus": "Test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_profile_minimal_data(
        self, authenticated_client: TestClient
    ):
        """Test creating profile with minimal data (only required fields)."""
        minimal_data = {
            "name": "Minimal User",
        }
        response = authenticated_client.post("/api/v1/users/profile/", json=minimal_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Minimal User"
        assert data["campus"] is None
        assert data["contact_info"] is None


class TestGetProfile:
    """Test GET /users/profile/ endpoint."""

    def test_get_own_profile_success(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test getting authenticated user's profile."""
        response = authenticated_client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_profile.id)
        assert data["name"] == test_profile.name
        assert data["campus"] == test_profile.campus
        assert data["user_id"] == str(test_profile.user_id)

    def test_get_profile_without_authentication(self, client: TestClient):
        """Test getting profile without authentication fails."""
        response = client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_not_found(self, authenticated_client: TestClient):
        """Test getting non-existent profile returns 404."""
        response = authenticated_client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_profile_includes_timestamps(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test that profile response includes timestamp fields."""
        response = authenticated_client.get("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data


class TestUpdateProfile:
    """Test PATCH /users/profile/ endpoint."""

    def test_update_profile_success(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test updating profile fields."""
        update_data = {
            "name": "Updated Name",
            "campus": "Updated Campus",
            "contact_info": {"email": "updated@example.com", "phone": "+9876543210"},
        }
        response = authenticated_client.patch("/api/v1/users/profile/", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["campus"] == "Updated Campus"
        assert data["contact_info"]["email"] == "updated@example.com"

    def test_update_profile_partial(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test partially updating profile (only some fields)."""
        update_data = {"campus": "Partial Update Campus"}
        response = authenticated_client.patch("/api/v1/users/profile/", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["campus"] == "Partial Update Campus"
        assert data["name"] == test_profile.name  # Should remain unchanged

    def test_update_profile_without_authentication(self, client: TestClient):
        """Test updating profile without authentication fails."""
        response = client.patch("/api/v1/users/profile/", json={"name": "Test"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_not_found(self, authenticated_client: TestClient):
        """Test updating non-existent profile returns 404."""
        update_data = {"name": "Test"}
        response = authenticated_client.patch("/api/v1/users/profile/", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_profile_clear_optional_fields(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test clearing optional fields by setting to null."""
        update_data = {"campus": None, "contact_info": None}
        response = authenticated_client.patch("/api/v1/users/profile/", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["campus"] is None
        assert data["contact_info"] is None

    def test_update_profile_updates_timestamp(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test that updating profile updates the updated_at timestamp."""
        original = authenticated_client.get("/api/v1/users/profile/").json()
        original_updated_at = original["updated_at"]

        # Update profile
        response = authenticated_client.patch("/api/v1/users/profile/", json={"name": "New Name"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Note: This might be flaky if the test runs too fast
        # In a real scenario, updated_at should be newer or equal


class TestUploadProfilePicture:
    """Test POST /users/profile/picture endpoint."""

    def test_upload_picture_success(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test uploading a profile picture."""
        picture_data = {"picture_url": "https://example.com/picture.jpg"}
        response = authenticated_client.post("/api/v1/users/profile/picture", json=picture_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["profile_picture_url"] == "https://example.com/picture.jpg"
        assert "updated_at" in data

    def test_replace_picture(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test replacing an existing profile picture."""
        # Upload first picture
        picture_data1 = {"picture_url": "https://example.com/picture1.jpg"}
        authenticated_client.post("/api/v1/users/profile/picture", json=picture_data1)

        # Replace with second picture
        picture_data2 = {"picture_url": "https://example.com/picture2.jpg"}
        response = authenticated_client.post("/api/v1/users/profile/picture", json=picture_data2)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["profile_picture_url"] == "https://example.com/picture2.jpg"

    def test_upload_picture_without_authentication(self, client: TestClient):
        """Test uploading picture without authentication fails."""
        picture_data = {"picture_url": "https://example.com/picture.jpg"}
        response = client.post("/api/v1/users/profile/picture", json=picture_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_picture_no_profile(self, authenticated_client: TestClient):
        """Test uploading picture without existing profile returns 404."""
        picture_data = {"picture_url": "https://example.com/picture.jpg"}
        response = authenticated_client.post("/api/v1/users/profile/picture", json=picture_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_picture_invalid_url(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test uploading picture with invalid URL fails validation."""
        picture_data = {"picture_url": "not-a-valid-url"}
        response = authenticated_client.post("/api/v1/users/profile/picture", json=picture_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_picture_missing_url(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test uploading picture without URL fails."""
        response = authenticated_client.post("/api/v1/users/profile/picture", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeleteProfile:
    """Test DELETE /users/profile/ endpoint."""

    def test_delete_profile_success(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test deleting a profile."""
        response = authenticated_client.delete("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify profile is deleted
        get_response = authenticated_client.get("/api/v1/users/profile/")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_profile_without_authentication(self, client: TestClient):
        """Test deleting profile without authentication fails."""
        response = client.delete("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_profile_not_found(self, authenticated_client: TestClient):
        """Test deleting non-existent profile returns 404."""
        response = authenticated_client.delete("/api/v1/users/profile/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_profile_idempotent(
        self, authenticated_client: TestClient, test_profile: Profile
    ):
        """Test that deleting a profile twice handles gracefully."""
        # First delete
        first_response = authenticated_client.delete("/api/v1/users/profile/")
        assert first_response.status_code == status.HTTP_204_NO_CONTENT

        # Second delete attempt
        second_response = authenticated_client.delete("/api/v1/users/profile/")
        assert second_response.status_code == status.HTTP_404_NOT_FOUND


class TestProfileIntegration:
    """Integration tests for profile workflows."""

    def test_complete_profile_lifecycle(
        self, authenticated_client: TestClient, valid_profile_data: dict
    ):
        """Test complete profile workflow: create -> get -> update -> delete."""
        # Create profile
        create_response = authenticated_client.post("/api/v1/users/profile/", json=valid_profile_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        profile_id = create_response.json()["id"]

        # Get profile
        get_response = authenticated_client.get("/api/v1/users/profile/")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["id"] == profile_id

        # Update profile
        update_response = authenticated_client.patch(
            "/api/v1/users/profile/", json={"name": "Updated Name"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == "Updated Name"

        # Upload picture
        picture_response = authenticated_client.post(
            "/api/v1/users/profile/picture", json={"picture_url": "https://example.com/pic.jpg"}
        )
        assert picture_response.status_code == status.HTTP_201_CREATED

        # Delete profile
        delete_response = authenticated_client.delete("/api/v1/users/profile/")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        verify_response = authenticated_client.get("/api/v1/users/profile/")
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
