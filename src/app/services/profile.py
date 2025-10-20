"""
Profile service.

This module contains business logic for profile operations.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.repository.profile import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    """Service for profile business logic."""

    def get_by_user_id(self, db: Session, user_id: int) -> Profile:
        profile = ProfileRepository.get_by_user_id(db, user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile with user ID {user_id} not found",
            )
        return profile

    def get_by_id(self, db: Session, profile_id: int) -> Profile:
        profile = ProfileRepository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile with profile ID {profile_id} not found",
            )
        return profile

    def create(self, db: Session, profile: ProfileCreate) -> Profile:
        existing_profile = ProfileRepository.get_by_id(db, profile.id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile is already created.",
            )
        return ProfileRepository.create(db, profile)

    def update(self, db: Session, profile: ProfileUpdate) -> Profile:
        pass

    def delete(self, db: Session, profile_id: int) -> None:
        profile = ProfileRepository.get_by_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {profile_id} not found",
            )
        ProfileRepository.delete(db, profile)


# Create a singleton instance
profile_service = ProfileService()
