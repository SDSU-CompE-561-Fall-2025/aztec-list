"""
Test authentication endpoints.

Tests for user registration, login, and token-based authentication.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


class TestRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client: TestClient, valid_user_data: dict):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/signup", json=valid_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == valid_user_data["username"]
        assert data["email"] == valid_user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password

    def test_register_duplicate_email(
        self, client: TestClient, test_user: User, valid_user_data: dict
    ):
        """Test registration with duplicate email fails."""
        valid_user_data["email"] = test_user.email

        response = client.post("/api/v1/auth/signup", json=valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username(
        self, client: TestClient, test_user: User, valid_user_data: dict
    ):
        """Test registration with duplicate username fails."""
        valid_user_data["username"] = test_user.username

        response = client.post("/api/v1/auth/signup", json=valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient, valid_user_data: dict):
        """Test registration with invalid email format fails."""
        valid_user_data["email"] = "not-an-email"

        response = client.post("/api/v1/auth/signup", json=valid_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields fails."""
        response = client.post("/api/v1/auth/signup", json={"username": "test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestLogin:
    """Test user login endpoint."""

    def test_login_success_with_username(self, client: TestClient, test_user: User):
        """Test successful login with username."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "testpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user.username

    def test_login_success_with_email(self, client: TestClient, test_user: User):
        """Test successful login with email."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.username, "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing credentials fails."""
        response = client.post("/api/v1/auth/login", data={"username": "test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestTokenAuthentication:
    """Test token-based authentication."""

    def test_access_protected_endpoint_with_token(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test accessing protected endpoint with valid token."""
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(test_user.id)

    def test_access_protected_endpoint_without_token(self, client: TestClient, test_listing):
        """Test accessing protected endpoint without token fails."""
        # Try to delete a listing without authentication
        response = client.delete(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient, test_listing):
        """Test accessing protected endpoint with invalid token fails."""
        client.headers["Authorization"] = "Bearer invalid-token"
        response = client.delete(f"/api/v1/listings/{test_listing.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
