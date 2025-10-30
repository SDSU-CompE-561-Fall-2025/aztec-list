# Testing Guide

This guide explains how to run and work with the test suite for the Aztec List backend API.

## Setup

### Install Test Dependencies

First, install the test dependencies using uv:

```powershell
uv sync --group test
```

This will install:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for FastAPI testing
- `pytest-cov` - Code coverage reporting

## Running Tests

### Run All Tests

```powershell
cd backend
uv run pytest
```

### Run with Verbose Output

```powershell
uv run pytest -v
```

### Run Specific Test File

```powershell
uv run pytest tests/test_auth.py
uv run pytest tests/test_listings.py
uv run pytest tests/test_listing_images.py
```

### Run Specific Test Class or Function

```powershell
# Run specific test class
uv run pytest tests/test_auth.py::TestLogin

# Run specific test function
uv run pytest tests/test_auth.py::TestLogin::test_login_success_with_username
```

### Run Tests by Marker

```powershell
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

## Code Coverage

### Generate Coverage Report

```powershell
# Terminal output
uv run pytest --cov=app --cov-report=term-missing

# HTML report (opens in browser)
uv run pytest --cov=app --cov-report=html
# Then open: backend/htmlcov/index.html
```

### View Coverage for Specific Module

```powershell
uv run pytest --cov=app.services --cov-report=term-missing
uv run pytest --cov=app.routes --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_auth.py             # Authentication and registration tests
├── test_users.py            # User CRUD operations tests
├── test_listings.py         # Listing CRUD and filtering tests
└── test_listing_images.py   # Image upload and management tests
```

## Available Fixtures

### Database Fixtures
- `db_session` - Clean database session for each test
- `client` - FastAPI TestClient

### User Fixtures
- `test_user` - Regular verified user
- `test_user_unverified` - Unverified user
- `test_admin` - Admin user
- `test_user_token` - JWT token for test user
- `test_admin_token` - JWT token for admin
- `authenticated_client` - Client with user auth headers
- `admin_client` - Client with admin auth headers

### Data Fixtures
- `test_profile` - User profile
- `test_listing` - Active listing
- `test_listing_inactive` - Inactive listing
- `other_user_listing` - Listing owned by different user
- `test_image` - Single image for listing
- `test_images` - Multiple images for listing

### Test Data Helpers
- `valid_user_data` - Valid user registration data
- `valid_listing_data` - Valid listing creation data
- `valid_profile_data` - Valid profile creation data
- `valid_image_data` - Valid image creation data

## Writing New Tests

### Test Class Structure

```python
class TestFeatureName:
    """Test description."""

    def test_success_case(self, authenticated_client, test_user):
        """Test successful operation."""
        response = authenticated_client.get("/api/v1/endpoint")

        assert response.status_code == 200
        assert response.json()["id"] == str(test_user.id)

    def test_failure_case(self, client):
        """Test failure scenario."""
        response = client.get("/api/v1/endpoint")

        assert response.status_code == 401
```

### Using Fixtures

```python
def test_with_fixtures(
    self,
    authenticated_client: TestClient,
    test_listing: Listing,
    valid_listing_data: dict
):
    """Test that uses multiple fixtures."""
    # Fixtures are automatically injected
    response = authenticated_client.post(
        "/api/v1/listings",
        json=valid_listing_data
    )
    assert response.status_code == 201
```

### Testing Error Cases

```python
def test_not_found(self, client):
    """Test 404 response."""
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/listings/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unauthorized(self, client, test_listing):
    """Test 401 response."""
    response = client.patch(
        f"/api/v1/listings/{test_listing.id}",
        json={"title": "New"}
    )

    assert response.status_code == 401

def test_validation_error(self, authenticated_client):
    """Test 422 validation error."""
    response = authenticated_client.post(
        "/api/v1/listings",
        json={"title": "Test"}  # Missing required fields
    )

    assert response.status_code == 422
```

## Debugging Tests

### Run with Print Statements

```powershell
uv run pytest -s
```

### Run with Python Debugger

```python
def test_something(self, client):
    import pdb; pdb.set_trace()
    response = client.get("/api/v1/endpoint")
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
8. **Good Coverage** - Aim for 80%+ code coverage on business logic

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
