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

## Backend Quickstart

### Requirements
- [uv](https://docs.astral.sh/uv/) installed
- Python **3.13** (recommended). `uv python install` will fetch it for you.

### Steps
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

# 5) Run the API (dev)
uv run fastapi dev src/app/main.py
```

**Important Notes**:
- Open http://127.0.0.1:8000/docs for Swagger UI
- Run `uv run uvicorn --app-dir src app.main:app --reload` to start the app without FastAPI dev wrapper
- The `.env` file lives at the **project root** (shared between backend/frontend)
- The `.venv/` directory lives in **`backend/`** (Python dependencies)
- **Always run backend commands from the `backend/` directory**

## Frontend Quickstart

### Requirements
- Node.js 20+ (Next.js runtime)
- [Bun](https://bun.sh/docs/installation) ≥ 1.1 *(optional, but the fastest way to install/run scripts)*

### Steps
```bash
# 1) From the repo root, hop into the frontend workspace
cd frontend

# 2) Install dependencies (prefer Bun)
bun install
# fallbacks: npm install | yarn install | pnpm install

# 3) Start the dev server
bun dev
# fallbacks: npm run dev | yarn dev | pnpm dev

# 4) Open your browser at the Next.js URL printed above
# (or go directly to http://localhost:3000)
```

- Bun is preferred, but the npm/yarn/pnpm commands listed in the comments behave the same if that fits your setup better.
- The `dev` script echoes `Dev server: http://localhost:3000` before handing off to Next.js so the link is always visible/clickable.
- Other scripts map 1:1: e.g., `bun run lint` ↔ `npm run lint`, `bun run build` ↔ `npm run build`, etc.

## Code Quality & Pre-commit Hooks

This monorepo uses the **[pre-commit](https://pre-commit.com/)** framework to enforce code quality standards across both backend (Python) and frontend (TypeScript/JavaScript). Pre-commit hooks run automatically on staged files when you commit, ensuring consistent formatting and catching common issues.

### One-Time Setup

**1. Install pre-commit** (run from repo root):
```bash
# Install the pre-commit tool
uv tool install pre-commit

# Install the git hooks
pre-commit install
```

**2. Install VS Code Extensions** (optional but recommended):

Open the workspace and install recommended extensions when prompted, or install manually:
- **Prettier** (`esbenp.prettier-vscode`) - Auto-format on save
- **ESLint** (`dbaeumer.vscode-eslint`) - Real-time linting for TypeScript/JavaScript
- **EditorConfig** (`editorconfig.editorconfig`) - Consistent editor settings
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`) - Tailwind autocomplete

The workspace settings (`.vscode/settings.json`) are already configured to:
- Format files on save with Prettier
- Trim trailing whitespace

**Note:** ESLint runs on commit via pre-commit hooks, not on save. This avoids unintended changes during development while still enforcing code quality standards.

### What Runs Automatically on Commit

Pre-commit hooks run **only on staged files** and are path-aware:

#### Backend Files (`backend/**/*.py`)
- ✅ **Ruff** - Fast Python linter and formatter
- ✅ **Check AST** - Validate Python syntax
- ✅ **Check docstrings** - Ensure docstring placement

#### Frontend Files (`frontend/**/*.{ts,tsx,js,jsx}`)
- ✅ **ESLint** - Lint and auto-fix TypeScript/JavaScript
- ✅ **Prettier** - Format code consistently

#### All Files
- ✅ **Check large files** - Prevent accidentally committing large files
- ✅ **Detect private keys** - Block commits with secrets
- ✅ **Fix line endings** - Normalize to LF
- ✅ **Trim trailing whitespace**
- ✅ **Fix end-of-file** - Ensure final newline
- ✅ **Validate JSON/YAML/TOML** - Check syntax

**If unfixable errors are found, the commit is blocked.** Fix the issues and try again.

### Manual Commands

#### Run Pre-commit Hooks Manually

```bash
# From repo root:

# Run all hooks on all files (useful for CI or initial setup)
pre-commit run --all-files

# Run only on staged files (same as what happens on commit)
pre-commit run

# Update hook versions
pre-commit autoupdate
```

#### Project-Specific Commands

For backend-specific commands (Ruff, Python linting), see [backend/README.md](backend/README.md)

For frontend-specific commands (ESLint, Prettier), see [frontend/README.md](frontend/README.md)

### Configuration Files

- **`.pre-commit-config.yaml`** (repo root) - Defines all hooks and which files they run on
- **`backend/pyproject.toml`** - Ruff configuration for Python linting/formatting
- **`frontend/.prettierrc`** - Prettier formatting rules
- **`frontend/eslint.config.mjs`** - ESLint linting rules
- **`frontend/.editorconfig`** - Editor settings (indentation, line endings)
- **`.vscode/settings.json`** - VS Code auto-format/auto-fix settings

## Testing

For detailed testing documentation, see:
- Backend: [backend/tests/README.md](backend/tests/README.md)
- Frontend: Coming soon

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
APP__DOCS_URL="/docs"      # Swagger UI path (set to null to disable)
APP__REDOC_URL="/redoc"    # ReDoc UI path (set to null to disable)
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

#### Listing Settings
```bash
# Maximum number of images allowed per listing
LISTING__MAX_IMAGES_PER_LISTING=10
```

### Important Notes:

- **Never commit your `.env` file** - It contains sensitive information
- The `.env.example` file is safe to commit and serves as a template
- Settings use nested delimiter `__` (e.g., `DB__DATABASE_URL` maps to `settings.db.database_url`)
- The application will fail to start if `JWT__SECRET_KEY` is not set
- CORS wildcard (`"*"`) is blocked when `CORS__ALLOW_CREDENTIALS=true` for security
- Logging settings support both human-readable and JSON formats
