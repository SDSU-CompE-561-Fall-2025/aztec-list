"""
Profile repository.

This module provides data access layer for profile operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
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

        # Update db with direct assignment
        if "name" in update_data:
            db_profile.name = update_data["name"]
        if "campus" in update_data:
            db_profile.campus = update_data["campus"]
        if "contact_info" in update_data:
            db_profile.contact_info = update_data["contact_info"]

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
