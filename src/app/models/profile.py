from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Profile(Base):
    """
    Profile model for extended user information.

    Stores additional user details like full name, campus, contact info,
    and profile picture URL. Has a one-to-one relationship with User.
    """

    __tablename__ = "profiles"

    # need to update to use UUID or some hash of user id (but integer works for now)
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    campus = Column(String, nullable=True)
    contact_info = Column(JSON, nullable=True)  # dict with "email", "phone", etc.
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",  # ensure Profile records are cleaned up when a User is deleted
    )
