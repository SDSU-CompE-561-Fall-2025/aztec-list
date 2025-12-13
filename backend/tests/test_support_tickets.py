"""
Test support ticket endpoints.

Tests for support ticket creation, retrieval, status updates,
and deletion with authentication and email sending scenarios.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.enums import TicketStatus
from app.models.support_ticket import SupportTicket
from app.models.user import User


@pytest.fixture
def test_ticket(db_session, test_user: User) -> SupportTicket:
    """Create a test support ticket."""
    ticket = SupportTicket(
        id=uuid.uuid4(),
        user_id=test_user.id,
        email=test_user.email,
        subject="Test ticket subject",
        message="This is a test support ticket message.",
        status=TicketStatus.OPEN,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def anonymous_ticket_data() -> dict:
    """Create test data for anonymous support ticket."""
    return {
        "email": "anonymous@example.edu",
        "subject": "Help with my account",
        "message": "I cannot log in to my account. Please help me reset my password.",
    }


@pytest.fixture
def authenticated_ticket_data() -> dict:
    """Create test data for authenticated user support ticket."""
    return {
        "email": "test@example.edu",
        "subject": "Bug report",
        "message": "I found a bug when trying to upload images to my listing.",
    }


class TestCreateSupportTicket:
    """Test support ticket creation endpoint."""

    @patch("app.core.email.email_service.send_support_ticket_confirmation")
    @patch("app.core.email.email_service.send_support_ticket_notification")
    def test_create_ticket_authenticated_success(
        self,
        mock_notification: MagicMock,
        mock_confirmation: MagicMock,
        client: TestClient,
        test_user_token: str,
        authenticated_ticket_data: dict,
    ):
        """Test successful ticket creation by authenticated user."""
        # Mock email sending success
        mock_confirmation.return_value = True
        mock_notification.return_value = True

        response = client.post(
            "/api/v1/support",
            json=authenticated_ticket_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == authenticated_ticket_data["email"]
        assert data["subject"] == authenticated_ticket_data["subject"]
        assert data["message"] == authenticated_ticket_data["message"]
        assert data["status"] == "open"
        assert data["email_sent"] is True
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

        # Verify both emails were sent
        mock_confirmation.assert_called_once()
        mock_notification.assert_called_once()

    @patch("app.core.email.email_service.send_support_ticket_confirmation")
    @patch("app.core.email.email_service.send_support_ticket_notification")
    def test_create_ticket_anonymous_success(
        self,
        mock_notification: MagicMock,
        mock_confirmation: MagicMock,
        client: TestClient,
        anonymous_ticket_data: dict,
    ):
        """Test successful ticket creation by anonymous user."""
        # Mock email sending success
        mock_confirmation.return_value = True
        mock_notification.return_value = True

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == anonymous_ticket_data["email"]
        assert data["subject"] == anonymous_ticket_data["subject"]
        assert data["message"] == anonymous_ticket_data["message"]
        assert data["status"] == "open"
        assert data["email_sent"] is True
        assert data["user_id"] is None  # Not linked to user account

        # Verify both emails were sent
        mock_confirmation.assert_called_once()
        mock_notification.assert_called_once()

    @patch("app.core.email.email_service.send_support_ticket_confirmation")
    @patch("app.core.email.email_service.send_support_ticket_notification")
    def test_create_ticket_email_failure(
        self,
        mock_notification: MagicMock,
        mock_confirmation: MagicMock,
        client: TestClient,
        anonymous_ticket_data: dict,
    ):
        """Test ticket creation when email sending fails."""
        # Mock email sending failure
        mock_confirmation.return_value = False
        mock_notification.return_value = False

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email_sent"] is False  # Email failed but ticket was created
        assert data["email"] == anonymous_ticket_data["email"]

    def test_create_ticket_invalid_email(self, client: TestClient, anonymous_ticket_data: dict):
        """Test ticket creation with invalid email format."""
        anonymous_ticket_data["email"] = "not-a-valid-email"

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_ticket_subject_too_short(self, client: TestClient, anonymous_ticket_data: dict):
        """Test ticket creation with subject too short."""
        anonymous_ticket_data["subject"] = "Hi"  # Less than 3 characters

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_ticket_subject_too_long(self, client: TestClient, anonymous_ticket_data: dict):
        """Test ticket creation with subject too long."""
        anonymous_ticket_data["subject"] = "x" * 201  # More than 200 characters

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_ticket_message_too_short(self, client: TestClient, anonymous_ticket_data: dict):
        """Test ticket creation with message too short."""
        anonymous_ticket_data["message"] = "Help"  # Less than 10 characters

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_ticket_message_too_long(self, client: TestClient, anonymous_ticket_data: dict):
        """Test ticket creation with message too long."""
        anonymous_ticket_data["message"] = "x" * 2001  # More than 2000 characters

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_ticket_missing_fields(self, client: TestClient):
        """Test ticket creation with missing required fields."""
        response = client.post("/api/v1/support", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetSupportTickets:
    """Test support ticket retrieval endpoints."""

    def test_get_all_tickets_as_admin(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test retrieving all tickets as admin."""
        response = client.get(
            "/api/v1/support", headers={"Authorization": f"Bearer {test_admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_ticket.id)
        assert data[0]["subject"] == test_ticket.subject

    def test_get_all_tickets_as_user_forbidden(
        self, client: TestClient, test_user_token: str, test_ticket: SupportTicket
    ):
        """Test that regular users cannot view all tickets."""
        response = client.get(
            "/api/v1/support", headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all_tickets_unauthenticated(self, client: TestClient, test_ticket: SupportTicket):
        """Test that unauthenticated users cannot view tickets."""
        response = client.get("/api/v1/support")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_tickets_pagination(
        self, db_session, client: TestClient, test_admin_token: str, test_user: User
    ):
        """Test pagination when retrieving tickets."""
        # Create 5 tickets
        for i in range(5):
            ticket = SupportTicket(
                id=uuid.uuid4(),
                user_id=test_user.id,
                email=test_user.email,
                subject=f"Test ticket {i}",
                message=f"Test message {i}",
                status=TicketStatus.OPEN,
            )
            db_session.add(ticket)
        db_session.commit()

        # Get first 3 tickets
        response = client.get(
            "/api/v1/support?skip=0&limit=3",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

        # Get next 2 tickets
        response = client.get(
            "/api/v1/support?skip=3&limit=3",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_ticket_by_id_as_admin(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test retrieving specific ticket by ID as admin."""
        response = client.get(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_ticket.id)
        assert data["subject"] == test_ticket.subject
        assert data["message"] == test_ticket.message

    def test_get_ticket_by_id_as_user_forbidden(
        self, client: TestClient, test_user_token: str, test_ticket: SupportTicket
    ):
        """Test that regular users cannot view specific tickets."""
        response = client.get(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_ticket_by_id_not_found(self, client: TestClient, test_admin_token: str):
        """Test retrieving non-existent ticket."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/support/{fake_id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_ticket_by_id_invalid_uuid(self, client: TestClient, test_admin_token: str):
        """Test retrieving ticket with invalid UUID."""
        response = client.get(
            "/api/v1/support/not-a-uuid",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateTicketStatus:
    """Test support ticket status update endpoint."""

    def test_update_status_as_admin(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test updating ticket status as admin."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_ticket.id)
        assert data["status"] == "in_progress"

    def test_update_status_to_resolved(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test updating ticket status to resolved."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "resolved"},
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "resolved"

    def test_update_status_to_closed(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test updating ticket status to closed."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "closed"},
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "closed"

    def test_update_status_as_user_forbidden(
        self, client: TestClient, test_user_token: str, test_ticket: SupportTicket
    ):
        """Test that regular users cannot update ticket status."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "resolved"},
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_status_unauthenticated(self, client: TestClient, test_ticket: SupportTicket):
        """Test that unauthenticated users cannot update status."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "resolved"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_status_not_found(self, client: TestClient, test_admin_token: str):
        """Test updating status of non-existent ticket."""
        fake_id = uuid.uuid4()
        response = client.patch(
            f"/api/v1/support/{fake_id}/status",
            json={"status": "resolved"},
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_status_invalid_status(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test updating with invalid status value."""
        response = client.patch(
            f"/api/v1/support/{test_ticket.id}/status",
            json={"status": "INVALID_STATUS"},
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeleteTicket:
    """Test support ticket deletion endpoint."""

    def test_delete_ticket_as_admin(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket
    ):
        """Test deleting ticket as admin."""
        response = client.delete(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify ticket is deleted
        get_response = client.get(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_ticket_as_user_forbidden(
        self, client: TestClient, test_user_token: str, test_ticket: SupportTicket
    ):
        """Test that regular users cannot delete tickets."""
        response = client.delete(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_ticket_unauthenticated(self, client: TestClient, test_ticket: SupportTicket):
        """Test that unauthenticated users cannot delete tickets."""
        response = client.delete(f"/api/v1/support/{test_ticket.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_ticket_not_found(self, client: TestClient, test_admin_token: str):
        """Test deleting non-existent ticket."""
        fake_id = uuid.uuid4()
        response = client.delete(
            f"/api/v1/support/{fake_id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketWithUserRelationship:
    """Test support ticket relationships with users."""

    @patch("app.core.email.email_service.send_support_ticket_confirmation")
    @patch("app.core.email.email_service.send_support_ticket_notification")
    def test_ticket_linked_to_authenticated_user(
        self,
        mock_notification: MagicMock,
        mock_confirmation: MagicMock,
        client: TestClient,
        test_user: User,
        test_user_token: str,
        authenticated_ticket_data: dict,
    ):
        """Test that authenticated user's ticket is linked to their account."""
        mock_confirmation.return_value = True
        mock_notification.return_value = True

        response = client.post(
            "/api/v1/support",
            json=authenticated_ticket_data,
            headers={"Authorization": f"Bearer {test_user_token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(test_user.id)

    @patch("app.core.email.email_service.send_support_ticket_confirmation")
    @patch("app.core.email.email_service.send_support_ticket_notification")
    def test_ticket_not_linked_to_anonymous_user(
        self,
        mock_notification: MagicMock,
        mock_confirmation: MagicMock,
        client: TestClient,
        anonymous_ticket_data: dict,
    ):
        """Test that anonymous user's ticket has no user_id."""
        mock_confirmation.return_value = True
        mock_notification.return_value = True

        response = client.post("/api/v1/support", json=anonymous_ticket_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] is None

    def test_get_ticket_includes_user_data(
        self, client: TestClient, test_admin_token: str, test_ticket: SupportTicket, test_user: User
    ):
        """Test that retrieved ticket includes user relationship data."""
        response = client.get(
            f"/api/v1/support/{test_ticket.id}",
            headers={"Authorization": f"Bearer {test_admin_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["email"] == test_user.email
