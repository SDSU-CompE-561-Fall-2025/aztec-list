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
