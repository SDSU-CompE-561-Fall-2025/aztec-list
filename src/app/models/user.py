from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    User model for authentication and basic account information.

    Represents a registered user in the system with authentication credentials.
    Has a one-to-one relationship with Profile and one-to-many with Listings.
    """

    __tablename__ = "users"

    # need to update to use UUID or some hash of user id (but integer works for now)
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
