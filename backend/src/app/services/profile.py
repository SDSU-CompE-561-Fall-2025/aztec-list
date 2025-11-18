"""
Profile service.

This module contains business logic for profile operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.repository.profile import ProfileRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session

    from app.models.profile import Profile
    from app.schemas.profile import ProfileCreate, ProfilePictureUpdate, ProfileUpdate


class ProfileService:
    """Service for profile business logic."""

    def get_by_user_id(self, db: Session, user_id: uuid.UUID) -> Profile:
        """
        Get profile by user ID.

        Args:
            db: Database session
            user_id: User ID (UUID)

        Returns:
            Profile: Profile object

        Raises:
            HTTPException: If profile not found
        """
        profile = ProfileRepository.get_by_user_id(db, user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        return profile

    def get_by_id(self, db: Session, profile_id: uuid.UUID) -> Profile:
        """
        Get profile by ID.

        Args:
            db: Database session
            profile_id: Profile ID (UUID)

        Returns:
            Profile: Profile object

        Raises:
            HTTPException: If profile not found
        """
        profile = ProfileRepository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile with ID {profile_id} not found",
            )
        return profile

    def create(self, db: Session, user_id: uuid.UUID, profile: ProfileCreate) -> Profile:
        """
        Create a new profile for a user with validation.

        Args:
            db: Database session
            user_id: User ID to associate with profile
            profile: Profile creation data

        Returns:
            Profile: Created profile

        Raises:
            HTTPException: If profile already exists for this user
        """
        existing_profile = ProfileRepository.get_by_user_id(db, user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this user",
            )

        profile_data = profile.model_dump()
        if profile_data.get("profile_picture_url"):
            profile_data["profile_picture_url"] = str(profile_data["profile_picture_url"])

        return ProfileRepository.create(db, user_id, profile_data)

    def update(self, db: Session, user_id: uuid.UUID, profile: ProfileUpdate) -> Profile:
        """
        Update profile fields for a user.

        Args:
            db: Database session
            user_id: User ID whose profile to update
            profile: Profile update data (only provided fields will be updated)

        Returns:
            Profile: Updated profile

        Raises:
            HTTPException: If profile not found
        """
        db_profile = ProfileRepository.get_by_user_id(db, user_id)
        if not db_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user ID {user_id} not found",
            )

        update_data = profile.model_dump(exclude_unset=True)
        if update_data.get("profile_picture_url"):
            update_data["profile_picture_url"] = str(update_data["profile_picture_url"])

        return ProfileRepository.update(db, db_profile, update_data)

    def update_profile_picture(
        self, db: Session, user_id: uuid.UUID, data: ProfilePictureUpdate
    ) -> Profile:
        """
        Update profile picture URL for a user.

        Args:
            db: Database session
            user_id: User ID whose profile picture to update
            data: Profile picture update data with validated URL

        Returns:
            Profile: Updated profile

        Raises:
            HTTPException: If profile not found
        """
        db_profile = ProfileRepository.get_by_user_id(db, user_id)
        if not db_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user ID {user_id} not found",
            )
        return ProfileRepository.update_profile_picture(db, db_profile, str(data.picture_url))

    def delete(self, db: Session, user_id: uuid.UUID) -> None:
        """
        Delete a profile by user ID.

        Args:
            db: Database session
            user_id: User ID (UUID) whose profile to delete

        Raises:
            HTTPException: If profile not found
        """
        db_profile = ProfileRepository.get_by_user_id(db, user_id)
        if not db_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile for user ID {user_id} not found",
            )
        ProfileRepository.delete(db, db_profile)


# Create a singleton instance
profile_service = ProfileService()
