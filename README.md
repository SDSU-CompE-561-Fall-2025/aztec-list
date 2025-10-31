# Aztec List

## Overview
Aztec List is an OfferUp-style marketplace for college students. Students can post items with photos and descriptions, browse/search listings, and (in later iterations) coordinate sales via messaging. Prices are typically lower than MSRP.

## Project Structure

This is a monorepo containing both backend and frontend:

- **`backend/`** - FastAPI REST API (Python)
  - Has its own `.venv/` for Python dependencies
  - All backend commands run from `backend/` directory
- **`frontend/`** - Web frontend (coming soon)
  - Frontend commands will run from `frontend/` directory
- **`docs/`** - API documentation and design specs

## Backend Setup

### Requirements
- [uv](https://docs.astral.sh/uv/) installed
- Python **3.13** (recommended). `uv python install` will fetch it for you.

### Quickstart
```bash
# 1) Clone
git clone https://github.com/SDSU-CompE-561-Fall-2025/aztec-list.git
cd aztec-list

# 2) Configure environment variables (do this once at project root)
cp .env.example .env

# Generate a secure secret key and copy the output
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and replace JWT__SECRET_KEY with the generated key

# 3) Navigate to backend
cd backend

# 4) Install Python + sync deps from pyproject/uv.lock
uv python install
uv sync

# 5) (optional) Install Git hooks (ruff, EOF/line-endings, etc.)
uv run pre-commit install

# 6) Run the API (dev)
uv run fastapi dev src/app/main.py
```

**Important Notes**:
- Open http://127.0.0.1:8000/docs for Swagger UI
- Run `uv run uvicorn --app-dir src app.main:app --reload` to start the app without FastAPI dev wrapper
- The `.env` file lives at the **project root** (shared between backend/frontend)
- The `.venv/` directory lives in **`backend/`** (Python dependencies)
- **Always run backend commands from the `backend/` directory**

## Frontend Setup

The frontend will be developed in the `frontend/` directory. Instructions will be added once development begins.

## Environment Configuration

The application uses environment variables for configuration. These are loaded from a `.env` file in the project root.

### Setup Steps:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate a secure secret key:**
   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Edit `.env` and update the values:**
   - **Required:** `JWT__SECRET_KEY` - Use the key generated above
   - **Optional:** Modify database URL, token expiration, CORS origins, logging settings, etc.

### Configuration Options:

#### Security Settings (Required)
```bash
# IMPORTANT: Generate a secure key with:
# uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT__SECRET_KEY="your-generated-secret-key-here"
JWT__ALGORITHM="HS256"
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Database Settings
```bash
# SQLite (default for development):
DB__DATABASE_URL="sqlite:///./aztec_list.db"

# PostgreSQL (production):
# DB__DATABASE_URL="postgresql://user:password@localhost:5432/aztec_list"

DB__ECHO=false  # Set to true for SQL query logging
```

#### Application Settings
```bash
APP__TITLE="Aztec List"
APP__DESCRIPTION="API for an OfferUp-style marketplace for college students"
APP__VERSION="0.1.0"
```

#### CORS Settings
```bash
# WARNING: The default localhost origins are for DEVELOPMENT ONLY!
# In production, override with your actual frontend domain(s).
CORS__ALLOWED_ORIGINS='["http://localhost:3000"]'
CORS__ALLOW_CREDENTIALS=true
CORS__ALLOWED_METHODS='["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]'
CORS__ALLOWED_HEADERS='["*"]'

# NEVER use "*" (wildcard) with CORS__ALLOW_CREDENTIALS=true - this is a security risk!
```

#### Logging Settings
```bash
# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOGGING__LEVEL="INFO"
LOGGING__USE_JSON=false  # Use JSON format in production
LOGGING__FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOGGING__UVICORN_ACCESS_LEVEL="WARNING"
LOGGING__UVICORN_ERROR_LEVEL="INFO"
LOGGING__EXCLUDED_PATHS='["/health", "/docs", "/redoc", "/openapi.json"]'
```

#### Moderation Settings
```bash
# Number of strikes before automatic permanent ban
MODERATION__STRIKE_AUTO_BAN_THRESHOLD=3
```

### Important Notes:

- **Never commit your `.env` file** - It contains sensitive information
- The `.env.example` file is safe to commit and serves as a template
- Settings use nested delimiter `__` (e.g., `DB__DATABASE_URL` maps to `settings.db.database_url`)
- The application will fail to start if `JWT__SECRET_KEY` is not set
- CORS wildcard (`"*"`) is blocked when `CORS__ALLOW_CREDENTIALS=true` for security
- Logging settings support both human-readable and JSON formats
