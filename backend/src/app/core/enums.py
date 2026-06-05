"""
Application-wide enums.

This module contains all enum definitions used across models and schemas.
"""

import enum


class Category(str, enum.Enum):
    ELECTRONICS = "electronics"
    TEXTBOOKS = "textbooks"
    FURNITURE = "furniture"
    DORM = "dorm"
    APPLIANCES = "appliances"
    CLOTHING = "clothing"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    BIKES = "bicycles"
    SPORTS = "sports_equipment"
    TOOLS = "tools"
    OFFICE = "office_supplies"
    MUSIC = "music"
    MUSICAL_INSTRUMENTS = "musical_instruments"
    GAMES = "video_games"
    COLLECTIBLES = "collectibles"
    ART = "art"
    BABY = "baby_kids"
    PET_SUPPLIES = "pet_supplies"
    TICKETS = "tickets"
    SERVICES = "services"
    OTHER = "other"


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
    FLAG = "flag"


class UserRole(str, enum.Enum):
    """Enum for user roles."""

    USER = "user"
    ADMIN = "admin"


class LogLevel(str, enum.Enum):
    """Enum for logging levels matching Python's logging module."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TicketStatus(str, enum.Enum):
    """
    Enum for support ticket status.

    - OPEN: New ticket, not yet being worked on
    - IN_PROGRESS: Ticket is being actively worked on
    - RESOLVED: Issue has been resolved, waiting for user confirmation
    - CLOSED: Permanently closed, no further action needed
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AIMessageRole(str, enum.Enum):
    """Role of a message in an AI assistant conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class MessageReportCategory(str, enum.Enum):
    """Why a user reported a direct message."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    SCAM = "scam"
    HATE = "hate"
    NUDITY = "nudity"
    OTHER = "other"


class MessageReportStatus(str, enum.Enum):
    """
    Lifecycle of a user-submitted message report.

    - OPEN: Awaiting moderator review
    - DISMISSED: Reviewed, no action taken (false positive / not a violation)
    - UPHELD: Reviewed and actioned (a STRIKE was issued to the message author)
    """

    OPEN = "open"
    DISMISSED = "dismissed"
    UPHELD = "upheld"
