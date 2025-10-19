"""Models package - imports all models for SQLAlchemy."""

from app.models.profile import Profile
from app.models.user import User

__all__ = ["Profile", "User"]
