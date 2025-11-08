# Backend - Aztec List API

FastAPI REST API for the Aztec List marketplace.

## Quick Start

**Always run commands from the `backend/` directory!**

From the backend directory:

```bash
# First time setup: Install dependencies
uv sync

# Run development server
uv run fastapi dev src/app/main.py
```

## Environment Configuration

Environment variables are configured in `.env` at the **project root** (one level up from backend/).

To set up:
```bash
# From project root (not backend/)
cp .env.example .env

# Generate secret key
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and paste the generated key
```

See [Environment Configuration](../README.md#environment-configuration) in the main README.

## API Documentation

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
backend/
├── src/
│   └── app/
│       ├── core/          # Core functionality (config, security, database)
│       ├── models/        # SQLAlchemy models
│       ├── repository/    # Data access layer
│       ├── routes/        # API endpoints
│       ├── schemas/       # Pydantic schemas
│       └── services/      # Business logic
├── pyproject.toml         # Python dependencies
└── uv.lock               # Lock file
```

## Development

### Testing

```bash
# First time: Install test dependencies
uv sync --group test

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src/app --cov-report=html

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/ --ignore=tests/unit/

# Run specific test file
uv run pytest tests/test_users.py -v
```

**Test Coverage:**
- **387 tests total** with **98% code coverage**
- 210 unit tests (business logic, data access, core security)
- 177 integration tests (covering routes, auth, middleware)

See [Testing Guide](tests/README.md) for detailed testing documentation.

### Manual API Testing

Interactive API documentation with built-in testing:

```bash
# Start the development server
uv run fastapi dev src/app/main.py

# Open Swagger UI in your browser
# http://127.0.0.1:8000/docs
```

**Using Swagger UI for Manual Testing:**
1. Navigate to http://127.0.0.1:8000/docs
2. Click "Authorize" button to authenticate (if needed)
3. Expand any endpoint and click "Try it out"
4. Fill in parameters and request body
5. Click "Execute" to send the request
6. Review the response, status code, and headers

All 27 API endpoints have been manually tested using Swagger UI.

### Code Quality

```bash
# Run linter
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit Hooks

```bash
uv run pre-commit install
```

## Environment Variables

Environment variables are configured in the `.env` file at the **project root** (not in backend/).

See [Environment Configuration](../README.md#environment-configuration) in the main README.
