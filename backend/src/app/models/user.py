from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import UserRole

if TYPE_CHECKING:
    from app.models.admin import AdminAction
    from app.models.conversation import Conversation
    from app.models.listing import Listing
    from app.models.profile import Profile
    from app.models.support_ticket import SupportTicket


class User(Base):
    """
    User model for authentication and basic account information.

    Represents a registered user in the system with authentication credentials.
    Has a one-to-one relationship with Profile and one-to-many with Listings.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verification_token: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    profile: Mapped[Profile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",  # Delete profile when user is deleted
        single_parent=True,
    )

    listings: Mapped[list[Listing]] = relationship(
        back_populates="seller", cascade="all, delete-orphan"
    )

    # one-to-many -> Admin actions performed by this user (when acting as admin)
    admin_actions_performed: Mapped[list[AdminAction]] = relationship(
        "AdminAction",
        foreign_keys="AdminAction.admin_id",
        back_populates="admin",
    )

    # one-to-many -> Admin actions received by this user (when being moderated)
    admin_actions_received: Mapped[list[AdminAction]] = relationship(
        "AdminAction",
        foreign_keys="AdminAction.target_user_id",
        back_populates="target_user",
    )

    # one-to-many -> Conversations where this user is user_1
    conversations_as_user_1: Mapped[list[Conversation]] = relationship(
        "Conversation",
        foreign_keys="Conversation.user_1_id",
        back_populates="user_1",
        lazy="select",
    )

    # one-to-many -> Conversations where this user is user_2
    conversations_as_user_2: Mapped[list[Conversation]] = relationship(
        "Conversation",
        foreign_keys="Conversation.user_2_id",
        back_populates="user_2",
        lazy="select",
    )

    # one-to-many -> Support tickets submitted by this user
    support_tickets: Mapped[list[SupportTicket]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
