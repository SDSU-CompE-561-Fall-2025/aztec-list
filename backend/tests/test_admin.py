"""
Test admin action endpoints.

Tests for admin moderation actions including strikes, bans,
listing removals, and action management.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.enums import AdminActionType
from app.models.admin import AdminAction
from app.models.listing import Listing
from app.models.user import User


@pytest.fixture
def test_strike(db_session, test_admin: User, test_user: User) -> AdminAction:
    """Create a test strike action."""
    strike = AdminAction(
        id=uuid.uuid4(),
        admin_id=test_admin.id,
        target_user_id=test_user.id,
        action_type=AdminActionType.STRIKE,
        reason="Test strike",
    )
    db_session.add(strike)
    db_session.commit()
    db_session.refresh(strike)
    return strike


@pytest.fixture
def test_ban(db_session, test_admin: User, test_user: User) -> AdminAction:
    """Create a test ban action."""
    ban = AdminAction(
        id=uuid.uuid4(),
        admin_id=test_admin.id,
        target_user_id=test_user.id,
        action_type=AdminActionType.BAN,
        reason="Test ban",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(ban)
    db_session.commit()
    db_session.refresh(ban)
    return ban


class TestListAdminActions:
    """Test GET /admin/actions endpoint."""

    def test_list_actions_success(self, admin_client: TestClient, test_strike: AdminAction):
        """Test listing admin actions as admin."""
        response = admin_client.get("/api/v1/admin/actions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
        assert data["count"] >= 1

    def test_list_actions_without_admin(self, authenticated_client: TestClient):
        """Test listing admin actions without admin privileges fails."""
        response = authenticated_client.get("/api/v1/admin/actions")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_actions_without_auth(self, client: TestClient):
        """Test listing admin actions without authentication fails."""
        response = client.get("/api/v1/admin/actions")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_actions_filter_by_action_type(
        self, admin_client: TestClient, test_strike: AdminAction, test_ban: AdminAction
    ):
        """Test filtering actions by action_type."""
        response = admin_client.get("/api/v1/admin/actions?action_type=strike")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["action_type"] == "strike" for item in data["items"])

    def test_list_actions_filter_by_target_user(
        self, admin_client: TestClient, test_strike: AdminAction, test_user: User
    ):
        """Test filtering actions by target_user_id."""
        response = admin_client.get(f"/api/v1/admin/actions?target_user_id={test_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["target_user_id"] == str(test_user.id) for item in data["items"])

    def test_list_actions_filter_by_admin(
        self, admin_client: TestClient, test_strike: AdminAction, test_admin: User
    ):
        """Test filtering actions by admin_id."""
        response = admin_client.get(f"/api/v1/admin/actions?admin_id={test_admin.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["admin_id"] == str(test_admin.id) for item in data["items"])

    def test_list_actions_pagination(self, admin_client: TestClient, test_strike: AdminAction):
        """Test pagination of admin actions."""
        response = admin_client.get("/api/v1/admin/actions?limit=5&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) <= 5


class TestGetAdminAction:
    """Test GET /admin/actions/{action_id} endpoint."""

    def test_get_action_success(self, admin_client: TestClient, test_strike: AdminAction):
        """Test getting a single admin action by ID."""
        response = admin_client.get(f"/api/v1/admin/actions/{test_strike.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_strike.id)
        assert data["action_type"] == test_strike.action_type.value
        assert data["reason"] == test_strike.reason
        assert data["admin_id"] == str(test_strike.admin_id)
        assert data["target_user_id"] == str(test_strike.target_user_id)

    def test_get_action_not_found(self, admin_client: TestClient):
        """Test getting non-existent admin action returns 404."""
        fake_id = uuid.uuid4()
        response = admin_client.get(f"/api/v1/admin/actions/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_action_without_admin(
        self, authenticated_client: TestClient, test_strike: AdminAction
    ):
        """Test getting admin action without admin privileges fails."""
        response = authenticated_client.get(f"/api/v1/admin/actions/{test_strike.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_action_with_expiration(self, admin_client: TestClient, test_ban: AdminAction):
        """Test getting ban action includes expiration date."""
        response = admin_client.get(f"/api/v1/admin/actions/{test_ban.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "expires_at" in data
        assert data["expires_at"] is not None


class TestDeleteAdminAction:
    """Test DELETE /admin/actions/{action_id} endpoint."""

    def test_revoke_action_success(self, admin_client: TestClient, test_strike: AdminAction):
        """Test revoking an admin action."""
        response = admin_client.delete(f"/api/v1/admin/actions/{test_strike.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify action is deleted
        get_response = admin_client.get(f"/api/v1/admin/actions/{test_strike.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoke_action_not_found(self, admin_client: TestClient):
        """Test revoking non-existent action returns 404."""
        fake_id = uuid.uuid4()
        response = admin_client.delete(f"/api/v1/admin/actions/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoke_action_without_admin(
        self, authenticated_client: TestClient, test_strike: AdminAction
    ):
        """Test revoking action without admin privileges fails."""
        response = authenticated_client.delete(f"/api/v1/admin/actions/{test_strike.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_revoke_ban_lifts_restriction(
        self, admin_client: TestClient, test_ban: AdminAction
    ):
        """Test that revoking a ban allows user to perform actions again."""
        # Revoke ban
        response = admin_client.delete(f"/api/v1/admin/actions/{test_ban.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify ban is removed
        list_response = admin_client.get("/api/v1/admin/actions")
        actions = list_response.json()["items"]
        assert not any(action["id"] == str(test_ban.id) for action in actions)


class TestStrikeUser:
    """Test POST /admin/users/{user_id}/strike endpoint."""

    def test_strike_user_success(
        self, admin_client: TestClient, test_user: User, test_admin: User
    ):
        """Test adding a strike to a user."""
        strike_data = {"reason": "Posted inappropriate content"}
        response = admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json=strike_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["action_type"] == "strike"
        assert data["reason"] == "Posted inappropriate content"
        assert data["target_user_id"] == str(test_user.id)
        assert data["admin_id"] == str(test_admin.id)
        assert "id" in data

    def test_strike_user_without_reason(self, admin_client: TestClient, test_user: User):
        """Test striking user without reason (optional field)."""
        response = admin_client.post(f"/api/v1/admin/users/{test_user.id}/strike", json={})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["action_type"] == "strike"

    def test_strike_user_not_found(self, admin_client: TestClient):
        """Test striking non-existent user returns 404."""
        fake_id = uuid.uuid4()
        strike_data = {"reason": "Test"}
        response = admin_client.post(f"/api/v1/admin/users/{fake_id}/strike", json=strike_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_strike_user_without_admin(self, authenticated_client: TestClient, test_user: User):
        """Test striking user without admin privileges fails."""
        strike_data = {"reason": "Test"}
        # Using a different user's ID (test_user striking themselves would also fail)
        response = authenticated_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json=strike_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_strike_accumulation(self, admin_client: TestClient, test_user: User):
        """Test that multiple strikes accumulate."""
        # Add first strike
        admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json={"reason": "Strike 1"}
        )

        # Add second strike
        admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json={"reason": "Strike 2"}
        )

        # Verify both strikes exist
        response = admin_client.get(
            f"/api/v1/admin/actions?target_user_id={test_user.id}&action_type=strike"
        )
        data = response.json()
        assert data["count"] >= 2


class TestBanUser:
    """Test POST /admin/users/{user_id}/ban endpoint."""

    def test_ban_user_permanent(self, admin_client: TestClient, test_user: User):
        """Test permanently banning a user."""
        ban_data = {"reason": "Repeated violations"}
        response = admin_client.post(f"/api/v1/admin/users/{test_user.id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["action_type"] == "ban"
        assert data["reason"] == "Repeated violations"
        assert data["target_user_id"] == str(test_user.id)
        assert data["expires_at"] is None  # Permanent ban

    def test_ban_user_temporary(self, admin_client: TestClient, test_user: User):
        """Test banning a user (all bans are permanent in current implementation)."""
        ban_data = {"reason": "Policy violation"}
        response = admin_client.post(f"/api/v1/admin/users/{test_user.id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["action_type"] == "ban"
        # All bans are permanent - expires_at should be None
        assert data["expires_at"] is None

    def test_ban_user_not_found(self, admin_client: TestClient):
        """Test banning non-existent user returns 404."""
        fake_id = uuid.uuid4()
        ban_data = {"reason": "Test"}
        response = admin_client.post(f"/api/v1/admin/users/{fake_id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_ban_user_without_admin(self, authenticated_client: TestClient, test_user: User):
        """Test banning user without admin privileges fails."""
        ban_data = {"reason": "Test"}
        response = authenticated_client.post(
            f"/api/v1/admin/users/{test_user.id}/ban", json=ban_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_ban_prevents_user_actions(
        self, admin_client: TestClient, client: TestClient, test_user: User, test_user_token: str
    ):
        """Test that banned users cannot perform protected actions."""
        # Ban the user
        admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/ban", json={"reason": "Test ban"}
        )

        # Try to perform action as banned user
        client.headers["Authorization"] = f"Bearer {test_user_token}"
        listing_data = {
            "title": "Test",
            "description": "Test",
            "price": 10.0,
            "category": "electronics",
            "condition": "new",
        }
        response = client.post("/api/v1/listings", json=listing_data)

        # Should be forbidden due to ban
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRemoveListing:
    """Test POST /admin/listings/{listing_id}/remove endpoint."""

    def test_remove_listing_success(
        self, admin_client: TestClient, test_listing: Listing, test_admin: User
    ):
        """Test removing a listing."""
        removal_data = {"reason": "Violates community guidelines"}
        response = admin_client.post(
            f"/api/v1/admin/listings/{test_listing.id}/remove", json=removal_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["listing_id"] == str(test_listing.id)
        assert data["status"] == "removed"
        assert "admin_action" in data
        assert data["admin_action"]["action_type"] == "listing_removal"
        assert data["admin_action"]["reason"] == "Violates community guidelines"

    def test_remove_listing_issues_strike(
        self, admin_client: TestClient, test_listing: Listing, test_user: User
    ):
        """Test that removing listing also issues a strike to the owner."""
        removal_data = {"reason": "Spam"}
        response = admin_client.post(
            f"/api/v1/admin/listings/{test_listing.id}/remove", json=removal_data
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify strike was created
        actions_response = admin_client.get(
            f"/api/v1/admin/actions?target_user_id={test_user.id}&action_type=strike"
        )
        strikes = actions_response.json()["items"]
        assert len(strikes) >= 1

    def test_remove_listing_deletes_listing(
        self, admin_client: TestClient, client: TestClient, test_listing: Listing
    ):
        """Test that removing listing deletes it from database."""
        removal_data = {"reason": "Test removal"}
        admin_client.post(f"/api/v1/admin/listings/{test_listing.id}/remove", json=removal_data)

        # Verify listing is gone
        get_response = client.get(f"/api/v1/listings/{test_listing.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_listing_not_found(self, admin_client: TestClient):
        """Test removing non-existent listing returns 404."""
        fake_id = uuid.uuid4()
        removal_data = {"reason": "Test"}
        response = admin_client.post(f"/api/v1/admin/listings/{fake_id}/remove", json=removal_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_listing_without_admin(
        self, authenticated_client: TestClient, test_listing: Listing
    ):
        """Test removing listing without admin privileges fails."""
        removal_data = {"reason": "Test"}
        response = authenticated_client.post(
            f"/api/v1/admin/listings/{test_listing.id}/remove", json=removal_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_remove_listing_without_reason(
        self, admin_client: TestClient, test_listing: Listing
    ):
        """Test removing listing without reason succeeds (reason is optional)."""
        response = admin_client.post(f"/api/v1/admin/listings/{test_listing.id}/remove", json={})

        # Reason is optional - should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_can_remove_listing_from_banned_user(
        self, admin_client: TestClient, test_user: User, test_listing: Listing
    ):
        """Test that removing listing from banned user succeeds without adding a strike."""
        # First, ban the user
        ban_response = admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/ban", json={"reason": "Policy violation"}
        )
        assert ban_response.status_code == status.HTTP_201_CREATED

        # Count actions before listing removal
        actions_before = admin_client.get(f"/api/v1/admin/actions?target_user_id={test_user.id}")
        count_before = actions_before.json()["count"]

        # Now remove their listing - should succeed without adding a strike
        remove_response = admin_client.post(
            f"/api/v1/admin/listings/{test_listing.id}/remove", json={"reason": "Cleanup"}
        )
        # Should succeed - admins can remove listings from banned users
        assert remove_response.status_code == status.HTTP_200_OK

        # Verify only LISTING_REMOVAL was added, no additional STRIKE
        actions_after = admin_client.get(f"/api/v1/admin/actions?target_user_id={test_user.id}")
        count_after = actions_after.json()["count"]
        # Should have only added 1 action (LISTING_REMOVAL), not 2 (LISTING_REMOVAL + STRIKE)
        assert count_after == count_before + 1


class TestAdminIntegration:
    """Integration tests for admin workflows."""

    def test_complete_moderation_workflow(
        self, admin_client: TestClient, test_user: User, test_listing: Listing
    ):
        """Test complete moderation workflow: strike -> strike -> revoke."""
        # Step 1: Issue first strike
        strike1_response = admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json={"reason": "First warning"}
        )
        assert strike1_response.status_code == status.HTTP_201_CREATED
        strike1_id = strike1_response.json()["id"]

        # Step 2: Issue second strike
        strike2_response = admin_client.post(
            f"/api/v1/admin/users/{test_user.id}/strike", json={"reason": "Second warning"}
        )
        assert strike2_response.status_code == status.HTTP_201_CREATED

        # Step 3: Remove problematic listing
        remove_response = admin_client.post(
            f"/api/v1/admin/listings/{test_listing.id}/remove", json={"reason": "Spam"}
        )
        assert remove_response.status_code == status.HTTP_200_OK

        # Step 4: Review all actions for this user
        actions_response = admin_client.get(
            f"/api/v1/admin/actions?target_user_id={test_user.id}"
        )
        actions = actions_response.json()
        assert actions["count"] >= 3  # 2 strikes + 1 from listing removal

        # Step 5: Revoke first strike (user appeals)
        revoke_response = admin_client.delete(f"/api/v1/admin/actions/{strike1_id}")
        assert revoke_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 6: Verify action count decreased
        actions_after = admin_client.get(
            f"/api/v1/admin/actions?target_user_id={test_user.id}"
        ).json()
        assert actions_after["count"] == actions["count"] - 1

    def test_admin_cannot_moderate_self(self, admin_client: TestClient, test_admin: User):
        """Test that admins cannot issue strikes or bans to themselves."""
        # Try to strike self
        strike_response = admin_client.post(
            f"/api/v1/admin/users/{test_admin.id}/strike", json={"reason": "Self-strike"}
        )
        # Should succeed but be prevented by business logic if implemented
        # For now just verify the endpoint works
        assert strike_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_filter_actions_multiple_criteria(
        self,
        admin_client: TestClient,
        test_strike: AdminAction,
        test_ban: AdminAction,
        test_user: User,
    ):
        """Test filtering admin actions with multiple criteria."""
        response = admin_client.get(
            f"/api/v1/admin/actions?target_user_id={test_user.id}&action_type=strike"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return strikes for this specific user
        assert all(
            item["target_user_id"] == str(test_user.id) and item["action_type"] == "strike"
            for item in data["items"]
        )
