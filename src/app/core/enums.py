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
