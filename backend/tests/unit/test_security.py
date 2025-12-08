"""Unit tests for core security functions."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.enums import UserRole
from app.core.security import (
    ensure_admin,
    ensure_can_moderate_user,
    ensure_resource_owner,
    ensure_verified,
)
from app.models.user import User


class TestEnsureAdmin:
    """Test ensure_admin function."""

    def test_ensure_admin_success(self):
        """Test that admin users pass the check."""
        user = User(
            id=uuid4(),
            email="admin@example.edu",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        # Should not raise
        ensure_admin(user)

    def test_ensure_admin_failure(self):
        """Test that non-admin users are rejected."""
        user = User(
            id=uuid4(),
            email="user@example.edu",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        with pytest.raises(HTTPException) as exc_info:
            ensure_admin(user)
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail


class TestEnsureVerified:
    """Test ensure_verified function."""

    def test_ensure_verified_success(self):
        """Test that verified users pass the check."""
        user = User(
            id=uuid4(),
            email="verified@example.edu",
            username="verified",
            hashed_password="hashed",
            is_verified=True,
        )
        # Should not raise
        ensure_verified(user)

    def test_ensure_verified_failure(self):
        """Test that unverified users are rejected."""
        user = User(
            id=uuid4(),
            email="unverified@example.edu",
            username="unverified",
            hashed_password="hashed",
            is_verified=False,
        )
        with pytest.raises(HTTPException) as exc_info:
            ensure_verified(user)
        assert exc_info.value.status_code == 403
        assert "Email verification required" in exc_info.value.detail


class TestEnsureCanModerateUser:
    """Test ensure_can_moderate_user function."""

    def test_ensure_can_moderate_user_success(self):
        """Test that regular users can be moderated."""
        target = User(
            id=uuid4(),
            email="target@example.edu",
            username="target",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        moderator = User(
            id=uuid4(),
            email="admin@example.edu",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        # Should not raise
        ensure_can_moderate_user(target, moderator)

    def test_ensure_can_moderate_user_self_moderation(self):
        """Test that admins cannot moderate themselves."""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="admin@example.edu",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        with pytest.raises(HTTPException) as exc_info:
            ensure_can_moderate_user(user, user)
        assert exc_info.value.status_code == 403
        assert "Cannot moderate admin accounts" in exc_info.value.detail

    def test_ensure_can_moderate_user_admin_target(self):
        """Test that admins cannot moderate other admins."""
        target_admin = User(
            id=uuid4(),
            email="admin1@example.edu",
            username="admin1",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        moderator_admin = User(
            id=uuid4(),
            email="admin2@example.edu",
            username="admin2",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        with pytest.raises(HTTPException) as exc_info:
            ensure_can_moderate_user(target_admin, moderator_admin)
        assert exc_info.value.status_code == 403
        assert "Cannot moderate admin accounts" in exc_info.value.detail


class TestEnsureResourceOwner:
    """Test ensure_resource_owner function."""

    def test_ensure_resource_owner_success(self):
        """Test that resource owner passes the check."""
        user_id = uuid4()
        # Should not raise when IDs match
        ensure_resource_owner(user_id, user_id, "listing")

    def test_ensure_resource_owner_failure(self):
        """Test that non-owner is rejected."""
        owner_id = uuid4()
        other_user_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            ensure_resource_owner(owner_id, other_user_id, "listing")
        assert exc_info.value.status_code == 403
        assert "Only the owner can modify this listing" in exc_info.value.detail

    def test_ensure_resource_owner_custom_resource_name(self):
        """Test that custom resource name appears in error message."""
        owner_id = uuid4()
        other_user_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            ensure_resource_owner(owner_id, other_user_id, "profile")
        assert exc_info.value.status_code == 403
        assert "Only the owner can modify this profile" in exc_info.value.detail

    def test_ensure_resource_owner_default_resource_name(self):
        """Test that default resource name is used when not specified."""
        owner_id = uuid4()
        other_user_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            ensure_resource_owner(owner_id, other_user_id)
        assert exc_info.value.status_code == 403
        assert "Only the owner can modify this resource" in exc_info.value.detail
