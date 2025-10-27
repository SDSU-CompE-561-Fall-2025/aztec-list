"""
Application-wide enums.

This module contains all enum definitions used across models and schemas.
"""

import enum


class Condition(str, enum.Enum):
    """Enum for listing condition."""

    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ListingSortOrder(str, enum.Enum):
    """Enum for listing sort order options."""

    RECENT = "recent"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class AdminActionType(str, enum.Enum):
    """Enum for admin action types."""

    STRIKE = "strike"
    BAN = "ban"
    LISTING_REMOVAL = "listing_removal"


class UserRole(str, enum.Enum):
    """Enum for user roles."""

    USER = "user"
    ADMIN = "admin"
