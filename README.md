# Aztec List

## Overview
Aztec List is an OfferUp-style marketplace for college students. Students can post items with photos and descriptions, browse/search listings, and (in later iterations) coordinate sales via messaging. Prices are typically lower than MSRP.

## Requirements
- [uv](https://docs.astral.sh/uv/) installed
- Python **3.13** (recommended). `uv python install` will fetch it for you.

## Quickstart
```bash
# 1) Clone
git clone https://github.com/SDSU-CompE-561-Fall-2025/aztec-list.git
cd aztec-list

# 2) Install Python + sync deps from pyproject/uv.lock
uv python install
uv sync

# 3) Configure environment variables
cp .env.example .env

# Generate a secure secret key and copy the output
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and replace A2__SECRET_KEY with the generated key

# 4) (optional) Install Git hooks (ruff, EOF/line-endings, etc.)
uv run pre-commit install

# 5) Run the API (dev)
uv run fastapi dev src/app/main.py
```
**Notes**:
- Open http://127.0.0.1:8000/docs for Swagger UI
- Run `uv run uvicorn --app-dir src app.main:app --reload` to start the app without FastAPI dev wrapper

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
   - **Required:** `A2__SECRET_KEY` - Use the key generated above
   - **Optional:** Modify database URL, token expiration, etc.

### Configuration Options:

#### Security Settings (Required)
```bash
# IMPORTANT: Generate a secure key with:
# uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
A2__SECRET_KEY="your-generated-secret-key-here"
A2__ALGORITHM="HS256"
A2__ACCESS_TOKEN_EXPIRE_MINUTES=30
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

### Important Notes:

- **Never commit your `.env` file** - It contains sensitive information
- The `.env.example` file is safe to commit and serves as a template
- Settings use nested delimiter `__` (e.g., `DB__DATABASE_URL` maps to `settings.db.database_url`)
- The application will fail to start if `A2__SECRET_KEY` is not set
