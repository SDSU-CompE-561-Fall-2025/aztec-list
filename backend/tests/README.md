# Testing Guide

This guide explains how to run and work with the test suite for the Aztec List backend API.

## Test Coverage Summary

**365 total tests with 97% code coverage**

- **186 unit tests** (88% coverage) - Business logic and data access
- **179 integration tests** (97% coverage) - HTTP endpoints and full workflows
- **All 27 API endpoints** manually tested via Swagger UI

### Coverage Breakdown
- **Business Logic**: 97-100% (services and repositories)
- **API Routes**: 100% (all HTTP endpoints)
- **Core Infrastructure**: 67-100% (auth, middleware, dependencies)

## Setup

### Install Test Dependencies

First, install the test dependencies using uv:

```powershell
uv sync
```

This includes:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage reporting
- `httpx` - HTTP client (via FastAPI TestClient)

## Running Tests

### Run All Tests

```powershell
cd backend
uv run pytest
```

### Run with Coverage

```powershell
# Terminal coverage report
uv run pytest --cov=src/app --cov-report=term
```

### Generate HTML Coverage Report

```powershell
# Generate and view HTML report
uv run pytest --cov=src/app --cov-report=html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### Run Unit vs Integration Tests

```powershell
# Unit tests only (business logic)
uv run pytest tests/unit/

# Integration tests only (API endpoints)
uv run pytest tests/ --ignore=tests/unit/
```

### Run Specific Test File

```powershell
uv run pytest tests/test_auth.py -v
uv run pytest tests/unit/test_user_service.py -v
```

### Run Specific Test Class or Function

```powershell
# Run specific test class
uv run pytest tests/test_auth.py::TestLogin -v

# Run specific test function
uv run pytest tests/test_auth.py::TestLogin::test_login_success_with_username -v
```

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and configuration
│
├── Integration Tests (179 tests)
├── test_auth.py                     # Authentication & registration (13 tests)
├── test_users.py                    # User CRUD operations (27 tests)
├── test_profiles.py                 # Profile CRUD & pictures (43 tests)
├── test_listings.py                 # Listing CRUD & filtering (27 tests)
├── test_listing_images.py           # Image upload & management (19 tests)
├── test_admin.py                    # Admin moderation actions (35 tests)
├── test_route_errors.py             # Error validation for all routes (19 tests)
│
└── unit/                            # Unit Tests (186 tests)
    ├── test_admin_repository.py     # Admin data access (20 tests)
    ├── test_admin_service.py        # Admin business logic (25 tests)
    ├── test_listing_repository.py   # Listing data access (28 tests)
    ├── test_listing_service.py      # Listing business logic (11 tests)
    ├── test_listing_image_repository.py  # Image data access (22 tests)
    ├── test_listing_image_service.py     # Image business logic (21 tests)
    ├── test_profile_repository.py   # Profile data access (14 tests)
    ├── test_profile_service.py      # Profile business logic (12 tests)
    ├── test_user_repository.py      # User data access (15 tests)
    └── test_user_service.py         # User business logic (18 tests)
```

### Test Coverage by Module

#### Unit Tests (Business Logic)

**Services** - Test business logic in isolation using mocks:
- `test_admin_service.py` - Admin action creation, validation, listing removal
- `test_listing_service.py` - Listing CRUD, filtering, pagination
- `test_listing_image_service.py` - Image upload, thumbnail generation, limits
- `test_profile_service.py` - Profile CRUD, picture handling
- `test_user_service.py` - User CRUD, authentication, validation

**Repositories** - Test data access patterns:
- `test_admin_repository.py` - Admin action queries and filters
- `test_listing_repository.py` - Listing queries, filtering, pagination
- `test_listing_image_repository.py` - Image queries and ownership checks
- `test_profile_repository.py` - Profile CRUD operations
- `test_user_repository.py` - User queries and authentication

#### Integration Tests (API Endpoints)

**Authentication (`test_auth.py`)**
- User registration (success, validation, duplicates)
- Login with username/email
- Token-based authentication
- Password validation

**Users (`test_users.py`)**
- **GET /users/me** - Get current authenticated user
- **GET /users/{user_id}** - Get user by ID (public profile)
- **GET /users/{user_id}/listings** - Get user's listings with pagination
- **PATCH /users/me** - Update current user (username, email)
- **DELETE /users/me** - Delete user account
- Duplicate detection, validation, cascading deletes

**Profiles (`test_profiles.py`)**
- **POST /users/profile/** - Create user profile
- **GET /users/profile/** - Get own profile
- **PATCH /users/profile/** - Update profile fields
- **POST /users/profile/picture** - Upload/replace profile picture
- **DELETE /users/profile/** - Delete profile
- Field validation, timestamps, optional fields

**Listings (`test_listings.py`)**
- **POST /listings/** - Create new listing
- **GET /listings/** - Search/filter listings (category, condition, price, query)
- **GET /listings/{listing_id}** - Get single listing with images
- **PATCH /listings/{listing_id}** - Update listing (owner only)
- **DELETE /listings/{listing_id}** - Delete listing (owner only)
- Pagination, filtering, ownership checks

**Listing Images (`test_listing_images.py`)**
- **POST /listings/{listing_id}/images** - Add image to listing
- **GET /listings/{listing_id}/images/{image_id}** - Get single image
- **PATCH /listings/{listing_id}/images/{image_id}** - Update image
- **DELETE /listings/{listing_id}/images/{image_id}** - Delete image
- Thumbnail management, max image limits, ownership

**Admin (`test_admin.py`)**
- **GET /admin/actions** - List all moderation actions with filters
- **GET /admin/actions/{action_id}** - Get single action details
- **DELETE /admin/actions/{action_id}** - Revoke/delete admin action
- **POST /admin/users/{user_id}/strike** - Issue strike to user
- **POST /admin/users/{user_id}/ban** - Ban user (permanent only)
- **POST /admin/listings/{listing_id}/remove** - Remove listing + issue strike
- Strike auto-escalation, ban enforcement, moderation workflows

**Route Errors (`test_route_errors.py`)**
- Invalid UUID parameters across all routes
- Missing required fields in request bodies
- Invalid data types (strings for integers, etc.)
- Empty request bodies
- Query parameter validation
- Ensures proper error responses (400, 404, 422)

## Test Fixtures

### Shared Fixtures (`conftest.py`)

#### Integration Test Fixtures
- `db_session`: Async database session with automatic rollback
- `test_client`: HTTP client for API endpoint testing
- `test_user_data`: Sample user registration data
- `test_user`: Pre-created test user
- `test_user_token`: Authentication token for test user
- `admin_user`: Pre-created admin user
- `admin_token`: Authentication token for admin user
- `second_user`: Additional test user for multi-user scenarios

#### Unit Test Fixtures
- `mock_db_session`: Mock database session for unit tests
- `mock_user_repo`: Mock user repository
- `mock_profile_repo`: Mock profile repository
- `mock_listing_repo`: Mock listing repository
- `mock_listing_image_repo`: Mock listing image repository
- `mock_admin_repo`: Mock admin repository
- `user_service`: User service with mocked dependencies
- `profile_service`: Profile service with mocked dependencies
- `listing_service`: Listing service with mocked dependencies
- `listing_image_service`: Listing image service with mocked dependencies
- `admin_service`: Admin service with mocked dependencies

## Manual API Testing

### Swagger UI Testing

All 27 API endpoints have been manually tested using the interactive Swagger UI:

```powershell
# Start the development server
cd backend
uv run fastapi dev src/app/main.py

# Open Swagger UI in browser
start http://127.0.0.1:8000/docs  # Windows
open http://127.0.0.1:8000/docs   # macOS
```

**Testing Workflow:**
1. Create a test user via `/auth/register`
2. Login via `/auth/login` to get JWT token
3. Click "Authorize" button and paste token
4. Test authenticated endpoints (users, profiles, listings)
5. Test admin endpoints with admin token
6. Verify responses, error handling, and data validation

All endpoints tested for:
- Valid input handling
- Authentication requirements
- Error responses (400, 401, 403, 404, 422)
- Data validation
- Edge cases (empty strings, null values, etc.)

## Writing New Tests

### Unit Test Structure

```python
# tests/unit/test_feature_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.feature import FeatureService
from app.models.feature import Feature

class TestFeatureServiceCreate:
    """Test feature creation business logic."""

    @pytest.mark.asyncio
    async def test_create_success(self, feature_service, mock_feature_repo):
        """Test successful feature creation."""
        # Arrange
        data = {"name": "Test"}
        mock_feature_repo.create.return_value = Feature(id=1, name="Test")

        # Act
        result = await feature_service.create(data)

        # Assert
        assert result.name == "Test"
        mock_feature_repo.create.assert_called_once()
```

### Integration Test Structure

```python
# tests/test_feature.py
import pytest

class TestFeatureEndpoint:
    """Test feature API endpoint."""

    def test_success_case(self, test_client, test_user_token):
        """Test successful API call."""
        response = test_client.get(
            "/api/v1/feature",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        assert "name" in response.json()

    def test_unauthorized(self, test_client):
        """Test authentication required."""
        response = test_client.get("/api/v1/feature")

        assert response.status_code == 401
```

### Using Fixtures

```python
def test_with_fixtures(
    self,
    test_client: TestClient,
    test_listing: Listing,
    valid_listing_data: dict
):
    """Test that uses multiple fixtures."""
    # Fixtures are automatically injected
    response = test_client.post(
        "/api/v1/listings",
        json=valid_listing_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
```

### Testing Error Cases

```python
def test_not_found(self, test_client):
    """Test 404 response."""
    fake_id = uuid.uuid4()
    response = test_client.get(f"/api/v1/listings/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unauthorized(self, test_client, test_listing):
    """Test 401 response."""
    response = test_client.patch(
        f"/api/v1/listings/{test_listing.id}",
        json={"title": "New"}
    )

    assert response.status_code == 401

def test_validation_error(self, test_client, test_user_token):
    """Test 422 validation error."""
    response = test_client.post(
        "/api/v1/listings",
        json={"title": "Test"},  # Missing required fields
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 422
```

## Testing Philosophy

### Unit Tests vs Integration Tests

**Unit Tests (88% coverage):**
- Test business logic in isolation
- Use mocks for external dependencies
- Focus on services and repositories
- Fast execution
- Test edge cases and error handling

**Integration Tests (97% coverage):**
- Test full HTTP request/response cycle
- Use real database (with rollback)
- Test authentication and middleware
- Verify API contracts
- Test multi-component interactions

**Why the coverage difference?**
- Unit tests focus on business logic only
- Integration tests cover infrastructure (auth, middleware, routes)
- Both are essential for comprehensive testing
- No need to unit test route handlers (integration tests cover them)

## Debugging Tests

### Run with Print Statements

```powershell
uv run pytest -s
```

### Run with Python Debugger

```python
def test_something(self, test_client):
    import pdb; pdb.set_trace()
    response = test_client.get("/api/v1/endpoint")
```

### View Full Error Output

```powershell
uv run pytest --tb=long
```

## Continuous Integration

The tests are configured to run automatically via pre-commit hooks. To set up:

```powershell
uv run pre-commit install
```

Now tests will run before each commit.

## Best Practices

1. **Test Independence** - Each test should be independent and not rely on other tests
2. **Clean State** - Use fixtures to create fresh data for each test
3. **Descriptive Names** - Test names should clearly describe what they test
4. **Arrange-Act-Assert** - Structure tests in three clear sections
5. **Test Both Paths** - Test success cases AND error cases
6. **Mock External Services** - Don't make real API calls or send emails
7. **Fast Tests** - Keep tests fast by using in-memory database
8. **Good Coverage** - Aim for 90%+ code coverage on business logic (currently at 93%)
9. **Test Edge Cases** - Include tests for duplicate data, missing fields, invalid UUIDs
10. **Integration Tests** - Include complete workflow tests that cover multiple operations

## Troubleshooting

### Tests Fail with Import Errors

Make sure you've installed test dependencies:
```powershell
uv sync --group test
```

### Database Issues

Tests use an in-memory SQLite database that's created fresh for each test. If you see database errors, check that:
1. Models are properly imported in conftest.py
2. Relationships are correctly defined
3. Foreign key constraints are satisfied

### Authentication Issues

If auth tests fail, verify:
1. JWT secret is set in settings
2. Password hashing is working correctly
3. Token expiration is reasonable for tests

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
