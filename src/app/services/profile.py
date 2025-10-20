"""
Profile service.

This module contains business logic for profile operations.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.repository.profile import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate


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
        # Check if profile already exists for this user
        existing_profile = ProfileRepository.get_by_user_id(db, user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this user",
            )

        return ProfileRepository.create(db, user_id, profile)

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

        return ProfileRepository.update(db, db_profile, profile)

    def update_profile_picture(self, db: Session, user_id: uuid.UUID, picture_url: str) -> Profile:
        """
        Update profile picture URL for a user.

        Args:
            db: Database session
            user_id: User ID whose profile picture to update
            picture_url: New profile picture URL

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

        return ProfileRepository.update_profile_picture(db, db_profile, picture_url)

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
