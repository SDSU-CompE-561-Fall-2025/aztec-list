"""
Moderation service.

This module contains business logic for content detection and moderation.
Simply checks content and blocks violations. No tracking or escalation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.enums import UserRole
from app.core.moderation import content_moderator

if TYPE_CHECKING:
    from app.models.user import User
    from app.schemas.listing import ListingCreate

logger = logging.getLogger(__name__)


@dataclass
class ModerationDecision:
    """Result of content moderation check."""

    is_allowed: bool
    violation_detected: bool
    reason: str | None = None


class ModerationService:
    """Service for content moderation."""

    def check_listing_content(
        self,
        user: User,
        listing_data: ListingCreate,
    ) -> ModerationDecision:
        """
        Check listing content for policy violations.

        Args:
            user: User creating the listing
            listing_data: Listing content to check

        Returns:
            ModerationDecision: Decision with violation information
        """
        # Run automated content check
        moderation_result = content_moderator.check_content(
            listing_data.title, listing_data.description
        )

        # No violation - allow listing
        if not moderation_result.is_violation:
            return ModerationDecision(
                is_allowed=True,
                violation_detected=False,
            )

        reason = moderation_result.reason or "Content policy violation"

        logger.warning(
            "User %s violation: %s",
            user.id,
            reason,
        )

        if user.role == UserRole.ADMIN:
            return ModerationDecision(
                is_allowed=True,
                violation_detected=True,
                reason=reason,
            )

        return ModerationDecision(
            is_allowed=False,
            violation_detected=True,
            reason=reason,
        )


# Create singleton instance
moderation_service = ModerationService()
