"""Integration tests for automated content moderation in listing creation."""


import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.listing import Listing
from app.repository.admin import AdminActionRepository


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestListingModerationIntegration:
    """Integration tests for listing creation with content moderation."""

    def test_clean_listing_creation_succeeds(self, client, db, auth_headers_verified):
        """Test that listings with clean content are created successfully."""
        listing_data = {
            "title": "Used Laptop for Sale",
            "description": "Dell laptop in great condition. Works perfectly, no issues.",
            "price": 500.00,
            "category": "electronics",
            "condition": "used_good",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == listing_data["title"]
        assert data["is_active"] is True

    def test_listing_with_weapon_keyword_rejected(self, client, db, auth_headers_verified):
        """Test that listing with weapon keywords is rejected."""
        listing_data = {
            "title": "Firearm for sale",
            "description": "High quality gun, never used",
            "price": 800.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "prohibited content" in response.json()["detail"].lower()

    def test_listing_with_drug_keyword_rejected(self, client, db, auth_headers_verified):
        """Test that listing with drug keywords is rejected."""
        listing_data = {
            "title": "Special product",
            "description": "Premium cocaine for sale, best quality",
            "price": 100.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "prohibited content" in response.json()["detail"].lower()

    def test_listing_with_counterfeit_keyword_rejected(self, client, db, auth_headers_verified):
        """Test that listing with counterfeit keywords is rejected."""
        listing_data = {
            "title": "Designer Handbag",
            "description": "Replica designer bag, looks authentic",
            "price": 50.00,
            "category": "fashion",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_listing_with_fake_id_rejected(self, client, db, auth_headers_verified):
        """Test that listing offering fake IDs is rejected."""
        listing_data = {
            "title": "Documents available",
            "description": "Fake ID with hologram, looks real",
            "price": 150.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_rejected_listing_creates_strike(
        self, client, db, auth_headers_verified, verified_user
    ):
        """Test that rejected listing creates a strike for the user."""
        initial_strikes = AdminActionRepository.count_strikes(db, verified_user.id)

        listing_data = {
            "title": "Items for sale",
            "description": "Selling stolen goods, contact me",
            "price": 100.00,
            "category": "other",
            "condition": "used_good",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Check that strike was created
        final_strikes = AdminActionRepository.count_strikes(db, verified_user.id)
        assert final_strikes == initial_strikes + 1

    def test_rejected_listing_not_visible(self, client, db, auth_headers_verified):
        """Test that rejected listing does not appear in public listings."""
        # Try to create a listing with banned content
        listing_data = {
            "title": "Special item",
            "description": "Firearm for sale, best price",
            "price": 500.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Check that no new listing appears in search
        search_response = client.get("/api/v1/listings")
        assert search_response.status_code == status.HTTP_200_OK

        listings = search_response.json()["listings"]
        # Verify the rejected listing is not in results
        for listing in listings:
            assert "firearm" not in listing["description"].lower()

    def test_multiple_violations_in_content(self, client, db, auth_headers_verified):
        """Test that content with multiple violations is rejected."""
        listing_data = {
            "title": "Everything must go",
            "description": "Selling guns, cocaine, and fake IDs. Great prices!",
            "price": 100.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Should mention the violations
        assert "prohibited content" in response.json()["detail"].lower()

    def test_ssn_pattern_in_description_rejected(self, client, db, auth_headers_verified):
        """Test that SSN patterns in description are rejected."""
        listing_data = {
            "title": "Information for sale",
            "description": "Contact info: 123-45-6789, call me",
            "price": 50.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_innocent_kitchen_knife_listing_allowed(self, client, db, auth_headers_verified):
        """Test that innocent mentions of knives (kitchen items) are allowed."""
        listing_data = {
            "title": "Kitchen Knife Block",
            "description": "Wooden knife holder set, holds 8 knives. Great for kitchen organization.",
            "price": 30.00,
            "category": "home",
            "condition": "used_good",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        # Should succeed because "knife sale" is not present
        assert response.status_code == status.HTTP_201_CREATED

    def test_knife_sale_explicitly_rejected(self, client, db, auth_headers_verified):
        """Test that 'knife sale' is explicitly rejected."""
        listing_data = {
            "title": "Knife sale - combat knives",
            "description": "Selling tactical knives",
            "price": 100.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_case_insensitive_moderation(self, client, db, auth_headers_verified):
        """Test that moderation is case-insensitive."""
        listing_data = {
            "title": "ITEM FOR SALE",
            "description": "SELLING MY GUN COLLECTION",
            "price": 500.00,
            "category": "other",
            "condition": "used_good",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_moderation_reason_included_in_response(self, client, db, auth_headers_verified):
        """Test that moderation rejection includes a reason."""
        listing_data = {
            "title": "Weapon for sale",
            "description": "Contact for details",
            "price": 200.00,
            "category": "other",
            "condition": "new",
        }

        response = client.post("/api/v1/listings", json=listing_data, headers=auth_headers_verified)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        detail = response.json()["detail"]
        assert "policy violation" in detail.lower()
        assert "prohibited content" in detail.lower()
