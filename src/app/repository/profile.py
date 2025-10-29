"""
Profile repository.

This module provides data access layer for profile operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.profile import Profile

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileRepository:
    """Repository for profile data access."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: uuid.UUID) -> Profile | None:
        """
        Get profile by user ID.

        Args:
            db: Database session
            user_id: User ID (UUID)

        Returns:
            Profile | None: Profile if found, None otherwise
        """
        query = select(Profile).where(Profile.user_id == user_id)
        return db.scalars(query).first()

    @staticmethod
    def get_by_id(db: Session, profile_id: uuid.UUID) -> Profile | None:
        """
        Get profile by ID.

        Args:
            db: Database session
            profile_id: Profile ID (UUID)

        Returns:
            Profile | None: Profile if found, None otherwise
        """
        return db.get(Profile, profile_id)

    @staticmethod
    def create(db: Session, user_id: uuid.UUID, profile: ProfileCreate) -> Profile:
        """
        Create a new profile for a user.

        Args:
            db: Database session
            user_id: User ID to associate with profile
            profile: Profile creation data

        Returns:
            Profile: Created profile
        """
        # Convert contact_info to dict if provided
        contact_info_dict = None
        if profile.contact_info:
            contact_info_dict = profile.contact_info.model_dump(exclude_none=True)

        db_profile = Profile(
            user_id=user_id,
            name=profile.name,
            campus=profile.campus,
            contact_info=contact_info_dict,
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update(db: Session, db_profile: Profile, profile: ProfileUpdate) -> Profile:
        """
        Update profile fields.

        Args:
            db: Database session
            db_profile: Profile instance to update
            profile: Profile update data (only provided fields will be updated)

        Returns:
            Profile: Updated profile
        """
        # Convert ProfileUpdate model fields into dictionary
        update_data = profile.model_dump(exclude_unset=True)

        # Update only the fields present in the request
        for field, value in update_data.items():
            setattr(db_profile, field, value)

        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update_profile_picture(db: Session, db_profile: Profile, picture_url: str) -> Profile:
        """
        Update profile picture URL.

        Args:
            db: Database session
            db_profile: Profile instance to update
            picture_url: New profile picture URL

        Returns:
            Profile: Updated profile
        """
        db_profile.profile_picture_url = picture_url
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def delete(db: Session, db_profile: Profile) -> None:
        """
        Delete profile.

        Args:
            db: Database session
            db_profile: Profile instance to delete
        """
        db.delete(db_profile)
        db.commit()
