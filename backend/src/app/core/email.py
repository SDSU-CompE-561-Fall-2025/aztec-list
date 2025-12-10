"""
Email service for sending emails via Resend.

This module provides a wrapper around the Resend API for sending
transactional emails, including support ticket notifications and
confirmations.
"""

import logging

import resend

from app.core.settings import settings

logger = logging.getLogger(__name__)


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
            resend.Emails.send(
                {
                    "from": settings.email.from_email,
                    "to": email,
                    "subject": "Support Ticket Received - Aztec List",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #1f2937;">Support Ticket Received</h2>
                        <p>Thank you for contacting Aztec List support. We have received your message and will respond as soon as possible.</p>

                        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Ticket ID:</strong> {ticket_id}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Subject:</strong> {subject}</p>
                        </div>

                        <p style="color: #6b7280; font-size: 14px;">
                            If you didn't submit this request, please ignore this email.
                        </p>

                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                            © 2025 Aztec List. All rights reserved.
                        </p>
                    </div>
                    """,
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
            user_info = f"{username} ({email})" if username else email
            # Get frontend URL from CORS settings for admin dashboard link
            frontend_url = settings.cors.allowed_origins[0] if settings.cors.allowed_origins else ""
            admin_url = f"{frontend_url}/admin" if frontend_url else "#"

            resend.Emails.send(
                {
                    "from": settings.email.from_email,
                    "to": settings.email.support_email,
                    "subject": f"New Support Ticket: {subject}",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #1f2937;">New Support Ticket</h2>

                        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Ticket ID:</strong> {ticket_id}</p>
                            <p style="margin: 10px 0 0 0;"><strong>From:</strong> {user_info}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Subject:</strong> {subject}</p>
                        </div>

                        <div style="background-color: #ffffff; padding: 15px; border: 1px solid #e5e7eb; border-radius: 8px;">
                            <p style="margin: 0;"><strong>Message:</strong></p>
                            <p style="margin: 10px 0 0 0; white-space: pre-wrap;">{message}</p>
                        </div>

                        <p style="margin-top: 20px;">
                            <a href="{admin_url}" style="background-color: #374151; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                View in Admin Dashboard
                            </a>
                        </p>
                    </div>
                    """,
                }
            )
        except Exception:
            logger.exception("Failed to send notification email for ticket %s", ticket_id)
            return False
        else:
            logger.info("Notification email sent to support team for ticket %s", ticket_id)
            return True


# Global email service instance
email_service = EmailService()
