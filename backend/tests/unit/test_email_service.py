"""Unit tests for EmailService."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.core.email import EmailService


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    @patch("app.core.email.resend")
    @patch("app.core.email.settings")
    def test_init_with_api_key(self, mock_settings, mock_resend):
        """Test initialization with API key sets resend.api_key."""
        mock_settings.email.resend_api_key = "test_api_key"

        EmailService()

        assert mock_resend.api_key == "test_api_key"

    @patch("app.core.email.resend")
    @patch("app.core.email.settings")
    def test_init_without_api_key(self, mock_settings, mock_resend):
        """Test initialization without API key doesn't set resend.api_key."""
        mock_settings.email.resend_api_key = None

        EmailService()

        # api_key should not be set
        # (we can't assert it's not set because patch doesn't track non-assignments)


class TestEmailServiceSupportTicketConfirmation:
    """Tests for send_support_ticket_confirmation."""

    @patch("app.core.email.settings")
    def test_disabled_email_returns_false(self, mock_settings):
        """Test that disabled email service returns False."""
        mock_settings.email.enabled = False
        mock_settings.email.resend_api_key = "test_key"

        service = EmailService()
        result = service.send_support_ticket_confirmation(
            email="user@test.com", subject="Test Subject", ticket_id="123"
        )

        assert result is False

    @patch("app.core.email.settings")
    def test_no_api_key_returns_false(self, mock_settings):
        """Test that missing API key returns False."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = None

        service = EmailService()
        result = service.send_support_ticket_confirmation(
            email="user@test.com", subject="Test Subject", ticket_id="123"
        )

        assert result is False

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_successful_send(self, mock_settings, mock_jinja_env, mock_resend):
        """Test successful email sending returns True."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Test Email</html>"
        mock_jinja_env.get_template.return_value = mock_template

        service = EmailService()
        result = service.send_support_ticket_confirmation(
            email="user@test.com", subject="Test Subject", ticket_id="123"
        )

        assert result is True
        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == "user@test.com"
        assert call_args["subject"] == "Support Ticket Received - Aztec List"
        assert call_args["html"] == "<html>Test Email</html>"

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_exception_returns_false(self, mock_settings, mock_jinja_env, mock_resend, caplog):
        """Test that exception during send returns False and logs error."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Test Email</html>"
        mock_jinja_env.get_template.return_value = mock_template

        mock_resend.Emails.send.side_effect = Exception("Network error")

        service = EmailService()
        with caplog.at_level(logging.ERROR):
            result = service.send_support_ticket_confirmation(
                email="user@test.com", subject="Test Subject", ticket_id="123"
            )

        assert result is False
        assert "Failed to send confirmation email" in caplog.text


class TestEmailServiceSupportTicketNotification:
    """Tests for send_support_ticket_notification."""

    @patch("app.core.email.settings")
    def test_disabled_email_returns_false(self, mock_settings):
        """Test that disabled email service returns False."""
        mock_settings.email.enabled = False
        mock_settings.email.resend_api_key = "test_key"

        service = EmailService()
        result = service.send_support_ticket_notification(
            email="user@test.com",
            username="testuser",
            subject="Test Subject",
            message="Test message",
            ticket_id="123",
        )

        assert result is False

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_successful_send_with_username(self, mock_settings, mock_jinja_env, mock_resend):
        """Test successful notification with username."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"
        mock_settings.email.support_email = "support@azteclist.com"
        mock_settings.cors.frontend_url = "http://localhost:3000"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Notification</html>"
        mock_jinja_env.get_template.return_value = mock_template

        service = EmailService()
        result = service.send_support_ticket_notification(
            email="user@test.com",
            username="testuser",
            subject="Test Subject",
            message="Test message",
            ticket_id="123",
        )

        assert result is True
        mock_template.render.assert_called_once_with(
            ticket_id="123",
            user_info="testuser (user@test.com)",
            subject="Test Subject",
            message="Test message",
            admin_url="http://localhost:3000/admin",
        )
        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == "support@azteclist.com"
        assert call_args["subject"] == "New Support Ticket: Test Subject"

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_successful_send_without_username(self, mock_settings, mock_jinja_env, mock_resend):
        """Test successful notification without username (anonymous user)."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"
        mock_settings.email.support_email = "support@azteclist.com"
        mock_settings.cors.frontend_url = "http://localhost:3000"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Notification</html>"
        mock_jinja_env.get_template.return_value = mock_template

        service = EmailService()
        result = service.send_support_ticket_notification(
            email="anonymous@test.com",
            username=None,
            subject="Test Subject",
            message="Test message",
            ticket_id="456",
        )

        assert result is True
        mock_template.render.assert_called_once_with(
            ticket_id="456",
            user_info="anonymous@test.com",  # No username, just email
            subject="Test Subject",
            message="Test message",
            admin_url="http://localhost:3000/admin",
        )

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_exception_returns_false(self, mock_settings, mock_jinja_env, mock_resend, caplog):
        """Test that exception during send returns False and logs error."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"
        mock_settings.email.support_email = "support@azteclist.com"
        mock_settings.cors.frontend_url = "http://localhost:3000"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Notification</html>"
        mock_jinja_env.get_template.return_value = mock_template

        mock_resend.Emails.send.side_effect = Exception("API error")

        service = EmailService()
        with caplog.at_level(logging.ERROR):
            result = service.send_support_ticket_notification(
                email="user@test.com",
                username="testuser",
                subject="Test Subject",
                message="Test message",
                ticket_id="123",
            )

        assert result is False
        assert "Failed to send notification email" in caplog.text


class TestEmailServiceEmailVerification:
    """Tests for send_email_verification."""

    @patch("app.core.email.settings")
    def test_disabled_email_returns_false(self, mock_settings):
        """Test that disabled email service returns False."""
        mock_settings.email.enabled = False
        mock_settings.email.resend_api_key = "test_key"

        service = EmailService()
        result = service.send_email_verification(
            email="user@test.com", username="testuser", verification_token="abc123"
        )

        assert result is False

    @patch("app.core.email.settings")
    def test_no_api_key_returns_false(self, mock_settings):
        """Test that missing API key returns False."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = None

        service = EmailService()
        result = service.send_email_verification(
            email="user@test.com", username="testuser", verification_token="abc123"
        )

        assert result is False

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_successful_send(self, mock_settings, mock_jinja_env, mock_resend):
        """Test successful verification email sending."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"
        mock_settings.cors.frontend_url = "http://localhost:3000"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Verify Email</html>"
        mock_jinja_env.get_template.return_value = mock_template

        service = EmailService()
        result = service.send_email_verification(
            email="user@test.com", username="testuser", verification_token="abc123"
        )

        assert result is True
        mock_template.render.assert_called_once()
        call_kwargs = mock_template.render.call_args[1]
        assert call_kwargs["username"] == "testuser"
        assert call_kwargs["verification_url"] == "http://localhost:3000/verify-email?token=abc123"
        assert "current_year" in call_kwargs

        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == "user@test.com"
        assert call_args["subject"] == "Verify Your Email - Aztec List"
        assert call_args["html"] == "<html>Verify Email</html>"

    @patch("app.core.email.resend")
    @patch("app.core.email.jinja_env")
    @patch("app.core.email.settings")
    def test_exception_returns_false(self, mock_settings, mock_jinja_env, mock_resend, caplog):
        """Test that exception during send returns False and logs error."""
        mock_settings.email.enabled = True
        mock_settings.email.resend_api_key = "test_key"
        mock_settings.email.from_email = "noreply@azteclist.com"
        mock_settings.cors.frontend_url = "http://localhost:3000"

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Verify Email</html>"
        mock_jinja_env.get_template.return_value = mock_template

        mock_resend.Emails.send.side_effect = Exception("Template error")

        service = EmailService()
        with caplog.at_level(logging.ERROR):
            result = service.send_email_verification(
                email="user@test.com", username="testuser", verification_token="abc123"
            )

        assert result is False
        assert "Failed to send verification email" in caplog.text
