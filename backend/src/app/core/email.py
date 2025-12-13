"""
Email service for sending emails via Resend.

This module provides a wrapper around the Resend API for sending
transactional emails, including support ticket notifications and
confirmations.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Set up Jinja2 environment for email templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self) -> None:
        """Initialize the email service with Resend API key."""
        if settings.email.resend_api_key:
            resend.api_key = settings.email.resend_api_key

    def send_support_ticket_confirmation(self, email: str, subject: str, ticket_id: str) -> bool:
        """
        Send confirmation email to user who submitted a support ticket.

        Args:
            email: User's email address
            subject: Subject of the support ticket
            ticket_id: ID of the created ticket

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not settings.email.enabled or not settings.email.resend_api_key:
            logger.info("Email service disabled or not configured, skipping confirmation email")
            return False

        try:
            # Render template with Jinja2 (automatic escaping enabled)
            template = jinja_env.get_template("support_ticket_confirmation.html")
            html_content = template.render(
                ticket_id=ticket_id,
                subject=subject,
                current_year=datetime.now(UTC).year,
            )

            resend.Emails.send(
                {
                    "from": settings.email.from_email,
                    "to": email,
                    "subject": "Support Ticket Received - Aztec List",
                    "html": html_content,
                }
            )
        except Exception:
            logger.exception(
                "Failed to send confirmation email to %s for ticket %s", email, ticket_id
            )
            return False
        else:
            logger.info("Confirmation email sent to %s for ticket %s", email, ticket_id)
            return True

    def send_support_ticket_notification(
        self, email: str, username: str | None, subject: str, message: str, ticket_id: str
    ) -> bool:
        """
        Send notification to support team about new ticket.

        Args:
            email: Submitter's email address
            username: Submitter's username (if logged in)
            subject: Subject of the support ticket
            message: Message content
            ticket_id: ID of the created ticket

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not settings.email.enabled or not settings.email.resend_api_key:
            logger.info("Email service disabled or not configured, skipping notification email")
            return False

        try:
            # Prepare user info string
            user_info = f"{username} ({email})" if username else email

            # Render template with Jinja2 (automatic escaping enabled)
            template = jinja_env.get_template("support_ticket_notification.html")
            html_content = template.render(
                ticket_id=ticket_id,
                user_info=user_info,
                subject=subject,
                message=message,
                admin_url=f"{settings.cors.frontend_url}/admin",
            )

            resend.Emails.send(
                {
                    "from": settings.email.from_email,
                    "to": settings.email.support_email,
                    "subject": f"New Support Ticket: {subject}",
                    "html": html_content,
                }
            )
        except Exception:
            logger.exception("Failed to send notification email for ticket %s", ticket_id)
            return False
        else:
            logger.info("Notification email sent to support team for ticket %s", ticket_id)
            return True

    def send_email_verification(self, email: str, username: str, verification_token: str) -> bool:
        """
        Send email verification link to user.

        Args:
            email: User's email address
            username: User's username
            verification_token: Unique verification token

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not settings.email.enabled or not settings.email.resend_api_key:
            logger.info("Email service disabled or not configured, skipping verification email")
            return False

        try:
            # Construct verification URL
            verification_url = (
                f"{settings.cors.frontend_url}/verify-email?token={verification_token}"
            )

            # Render template with Jinja2 (automatic escaping enabled)
            template = jinja_env.get_template("email_verification.html")
            html_content = template.render(
                username=username,
                verification_url=verification_url,
                current_year=datetime.now(UTC).year,
            )

            resend.Emails.send(
                {
                    "from": settings.email.from_email,
                    "to": email,
                    "subject": "Verify Your Email - Aztec List",
                    "html": html_content,
                }
            )
        except Exception:
            logger.exception("Failed to send verification email to %s", email)
            return False
        else:
            logger.info("Verification email sent to %s", email)
            return True


# Global email service instance
email_service = EmailService()
