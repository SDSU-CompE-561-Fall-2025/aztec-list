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

# 2) Configure backend environment variables
cd backend
cp .env.example .env

# Generate a secure secret key and copy the output
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and replace JWT__SECRET_KEY with the generated key

# 3) Install Python + sync deps from pyproject/uv.lock
uv python install
uv sync

# 4) Run the API (dev)
uv run fastapi dev src/app/main.py
```

**Important Notes**:

- Open http://127.0.0.1:8000/docs for Swagger UI
- Run `uv run uvicorn --app-dir src app.main:app --reload` to start the app without FastAPI dev wrapper
- The backend `.env` file lives in **`backend/`** directory
- The frontend `.env.local` file lives in **`frontend/`** directory
- The `.venv/` directory lives in **`backend/`** (Python dependencies)
- **Always run backend commands from the `backend/` directory**

## Frontend Quickstart

### Requirements

- Node.js 20+ (Next.js runtime)
- [Bun](https://bun.sh/docs/installation) ≥ 1.1 _(optional, but the fastest way to install/run scripts)_

### Steps

```bash
# 1) From the repo root, hop into the frontend workspace
cd frontend

# 2) Configure frontend environment variables
cp .env.example .env.local
# Edit .env.local if you need to change API URLs (defaults work for local dev)

# 3) Install dependencies (prefer Bun)
bun install
# fallbacks: npm install | yarn install | pnpm install

# 4) Start the dev server
bun dev
# fallbacks: npm run dev | yarn dev | pnpm dev

# 5) Open your browser at the Next.js URL printed above
# (or go directly to http://localhost:3000)
```

- Bun is preferred, but the npm/yarn/pnpm commands listed in the comments behave the same if that fits your setup better.
- The `dev` script echoes `Dev server: http://localhost:3000` before handing off to Next.js so the link is always visible/clickable.
- Other scripts map 1:1: e.g., `bun run lint` ↔ `npm run lint`, `bun run build` ↔ `npm run build`, etc.

## Code Quality & Pre-commit Hooks

This monorepo uses **[pre-commit](https://pre-commit.com/)** to enforce code quality standards. Hooks run automatically on commit for both backend (Python) and frontend (TypeScript).

### Setup

```bash
# Install pre-commit (from repo root)
uv tool install pre-commit
pre-commit install
```

### What Runs on Commit

- **Backend** (`backend/**/*.py`) - Ruff linter/formatter, Python syntax checks
- **Frontend** (`frontend/**/*.{ts,tsx,js,jsx}`) - ESLint, Prettier
- **All Files** - Trailing whitespace, line endings, large file checks, secret detection

### Manual Commands

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run only on staged files
pre-commit run
```

For detailed backend/frontend commands, see their respective READMEs.

## Testing

For detailed testing documentation, see:

- Backend: [backend/tests/README.md](backend/tests/README.md)
- Frontend: [frontend/README.md#testing](frontend/README.md#testing)

## Docker Deployment

Run the entire stack (backend + frontend + PostgreSQL) with Docker Compose:

```bash
# 1. Copy the example .env file
cp .env.example .env

# 2. Generate a secure JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Edit .env and update:
#    - JWT__SECRET_KEY: Paste the generated key
#    - POSTGRES_PASSWORD: Set a secure database password
#    - Optional: EMAIL__RESEND_API_KEY for email verification

# 4. Start all services (PostgreSQL + Backend + Frontend)
docker-compose up --build
```

**Access:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Configuration:**
All settings in `.env` (see `.env.example` for details):

- `JWT__SECRET_KEY` - **Required**: JWT signing key
- `POSTGRES_PASSWORD` - **Required**: Database password
- `EMAIL__RESEND_API_KEY` - Optional: Email verification (leave empty to disable)
- `CORS__ALLOWED_ORIGINS` - Update for production domain

**Useful commands:**

```bash
docker-compose logs -f          # View logs
docker-compose logs -f postgres # View database logs
docker-compose down             # Stop and remove containers
docker-compose down -v          # Stop and remove containers + database volume
docker-compose restart          # Restart services
```

**Database:**
PostgreSQL data is persisted in a Docker volume. Tables are created automatically on first startup.

## Environment Configuration

Environment variables are configured separately in each workspace:

- **Backend**: See [backend/README.md](backend/README.md) for `.env` setup
- **Frontend**: See [frontend/README.md](frontend/README.md) for `.env.local` setup

## Figma Designs
https://www.figma.com/design/xxKB8iGQkeVq52bCpRLhr4/AztecListDesign?m=auto&t=arGCKyiwbzpnVzJp-1
