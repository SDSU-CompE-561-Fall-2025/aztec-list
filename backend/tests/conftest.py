"""
Pytest configuration and shared fixtures.

This module provides test fixtures for database sessions, test clients,
and common test data used across all test modules.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import create_access_token, get_password_hash
from app.core.database import Base, get_db
from app.core.enums import Condition, UserRole
from app.main import app
from app.models.listing import Listing
from app.models.listing_image import Image
from app.models.profile import Profile
from app.models.user import User

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special settings for SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a clean database session for each test.

    Creates all tables, yields the session, then drops all tables after the test.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with overridden database dependency.

    Args:
        db_session: Test database session

    Yields:
        TestClient: FastAPI test client
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# User Fixtures
# ============================================================================


@pytest.fixture
def test_user(db_session: Session) -> User:
    """
    Create a test user in the database.

    Returns:
        User: Test user with username 'testuser'
    """
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_unverified(db_session: Session) -> User:
    """
    Create an unverified test user in the database.

    Returns:
        User: Unverified test user
    """
    user = User(
        id=uuid.uuid4(),
        username="unverifieduser",
        email="unverified@example.edu",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=False,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session: Session) -> User:
    """
    Create a test admin user in the database.

    Returns:
        User: Test admin user
    """
    admin = User(
        id=uuid.uuid4(),
        username="adminuser",
        email="admin@example.edu",
        hashed_password=get_password_hash("adminpassword123"),
        is_verified=True,
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """
    Generate JWT token for test user.

    Args:
        test_user: Test user fixture

    Returns:
        str: JWT access token
    """
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def test_admin_token(test_admin: User) -> str:
    """
    Generate JWT token for test admin.

    Args:
        test_admin: Test admin fixture

    Returns:
        str: JWT access token
    """
    return create_access_token({"sub": str(test_admin.id)})


@pytest.fixture
def authenticated_client(client: TestClient, test_user_token: str) -> TestClient:
    """
    Create a test client with authentication headers.

    Args:
        client: Test client fixture
        test_user_token: JWT token for test user

    Returns:
        TestClient: Client with authentication headers set
    """
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client


@pytest.fixture
def admin_client(client: TestClient, test_admin_token: str) -> TestClient:
    """
    Create a test client with admin authentication headers.

    Args:
        client: Test client fixture
        test_admin_token: JWT token for test admin

    Returns:
        TestClient: Client with admin authentication headers
    """
    client.headers["Authorization"] = f"Bearer {test_admin_token}"
    return client


# ============================================================================
# Profile Fixtures
# ============================================================================


@pytest.fixture
def test_profile(db_session: Session, test_user: User) -> Profile:
    """
    Create a test profile for test user.

    Args:
        db_session: Database session
        test_user: Test user fixture

    Returns:
        Profile: Test user's profile
    """
    profile = Profile(
        user_id=test_user.id,
        name="Test User",
        campus="Test University",
        contact_info={"email": "test@example.edu", "phone": "+1234567890"},
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


# ============================================================================
# Listing Fixtures
# ============================================================================


@pytest.fixture
def test_listing(db_session: Session, test_user: User) -> Listing:
    """
    Create a test listing for test user.

    Args:
        db_session: Database session
        test_user: Test user fixture

    Returns:
        Listing: Test listing
    """
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=test_user.id,
        title="Test Laptop",
        description="A great laptop for testing",
        price=500.00,
        category="electronics",
        condition=Condition.GOOD,
        is_active=True,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


@pytest.fixture
def test_listing_inactive(db_session: Session, test_user: User) -> Listing:
    """
    Create an inactive test listing.

    Args:
        db_session: Database session
        test_user: Test user fixture

    Returns:
        Listing: Inactive test listing
    """
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=test_user.id,
        title="Inactive Listing",
        description="This listing is not active",
        price=100.00,
        category="textbooks",
        condition=Condition.NEW,
        is_active=False,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


@pytest.fixture
def other_user_listing(db_session: Session) -> Listing:
    """
    Create a listing owned by a different user.

    Args:
        db_session: Database session

    Returns:
        Listing: Listing owned by another user
    """
    other_user = User(
        id=uuid.uuid4(),
        username="otheruser",
        email="other@example.edu",
        hashed_password=get_password_hash("password123"),
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(other_user)
    db_session.commit()

    listing = Listing(
        id=uuid.uuid4(),
        seller_id=other_user.id,
        title="Other User's Listing",
        description="You should not be able to edit this",
        price=200.00,
        category="furniture",
        condition=Condition.FAIR,
        is_active=True,
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


# ============================================================================
# Image Fixtures
# ============================================================================


@pytest.fixture
def test_image(db_session: Session, test_listing: Listing) -> Image:
    """
    Create a test image for test listing.

    Args:
        db_session: Database session
        test_listing: Test listing fixture

    Returns:
        Image: Test image
    """
    image = Image(
        id=uuid.uuid4(),
        listing_id=test_listing.id,
        url="https://example.com/image1.jpg",
        is_thumbnail=True,
        alt_text="Test image",
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)
    return image


@pytest.fixture
def test_images(db_session: Session, test_listing: Listing) -> list[Image]:
    """
    Create multiple test images for test listing.

    Args:
        db_session: Database session
        test_listing: Test listing fixture

    Returns:
        list[Image]: List of test images
    """
    images = []
    for i in range(3):
        image = Image(
            id=uuid.uuid4(),
            listing_id=test_listing.id,
            url=f"https://example.com/image{i + 1}.jpg",
            is_thumbnail=(i == 0),
            alt_text=f"Test image {i + 1}",
        )
        db_session.add(image)
        images.append(image)

    db_session.commit()
    for image in images:
        db_session.refresh(image)

    return images


# ============================================================================
# Test Data Helpers
# ============================================================================


@pytest.fixture
def valid_user_data() -> dict:
    """Valid user registration data."""
    return {
        "username": "newuser",
        "email": "newuser@example.edu",
        "password": "securepassword123",
    }


@pytest.fixture
def valid_listing_data() -> dict:
    """Valid listing creation data."""
    return {
        "title": "Test Item",
        "description": "A test item description",
        "price": 99.99,
        "category": "electronics",
        "condition": "new",
    }


@pytest.fixture
def valid_profile_data() -> dict:
    """Valid profile creation data."""
    return {
        "name": "John Doe",
        "campus": "UC San Diego",
        "contact_info": {
            "email": "john.doe@example.edu",
            "phone": "+1234567890",
        },
    }


@pytest.fixture
def valid_image_data() -> dict:
    """Valid image creation data."""
    return {
        "url": "https://example.com/test-image.jpg",
        "is_thumbnail": False,
        "alt_text": "Test image description",
    }
