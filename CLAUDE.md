# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git conventions

- **Commits: title only.** No body/description, no `Co-Authored-By` trailer. One concise subject line, **≤50 characters** (longer subjects wrap and look broken in git viewers).
- **Never open pull requests.** Do not run `gh pr create` (or any PR-opening command). Commit and push only; the user opens PRs themselves.

## Workspace layout — run commands in the right directory

Monorepo with two **independent** workspaces. There is no root-level package manager project; tooling is per-workspace.

- `backend/` — FastAPI REST API (Python, managed by `uv`). Run **all** backend commands from `backend/`.
- `frontend/` — Next.js App Router app (TypeScript, managed by `bun`). Run **all** frontend commands from `frontend/`.
- `docs/` — API design specs and `openapi.yaml`.

**Never run `bun`/`npm` from the repo root.** Bun walks up, treats the root as a phantom workspace, and creates stray root `node_modules/`, `package.json`, and `bun.lock`. Always `cd frontend` first. (The root `package-lock.json` is an empty placeholder, not a real project.)

## Backend (run from `backend/`)

```bash
uv python install && uv sync          # install runtime + dev deps
uv sync --group test                  # add the test-only deps (pytest, httpx, cov)
uv run fastapi dev src/app/main.py    # dev server → http://127.0.0.1:8000/docs
uv run ruff check src                 # lint  (config: select = ["ALL"], line-length 100)
uv run ruff format src                # format
uv run pytest                         # all tests (cov is on by default via addopts)
uv run pytest tests/unit/test_user_service.py::TestLogin::test_login_success_with_username -v   # single test
```

Python 3.13 required. `uv run` executes inside the project venv (`backend/.venv`).

### Backend architecture

Layered, with one file per domain (`user`, `listing`, `listing_image`, `message`, `conversation`, `profile`, `admin`, `support_ticket`) repeated across each layer:

```
routes/      FastAPI handlers (HTTP layer)        →
services/    business logic                        →
repository/  SQLAlchemy data access                →
models/      SQLAlchemy ORM tables
schemas/     Pydantic request/response models (I/O boundary)
```

- `api/v1/routes.py` aggregates every router under the `/api/v1` prefix. WebSocket routes (`routes/websocket_messages.py`) are mounted separately for real-time messaging.
- `core/` holds cross-cutting concerns: `settings.py`, `database.py`, `dependencies.py` (FastAPI DI), `auth.py`/`security.py` (JWT + argon2 via pwdlib), `rate_limiter.py` (slowapi), `email.py` (Resend), `storage.py`/`image_processing.py` (uploads + Pillow), `moderation.py`, `middleware.py`, `websocket.py`.
- **Config** is `pydantic-settings` with nested env vars using a `__` delimiter — e.g. `JWT__SECRET_KEY`, `CORS__ALLOWED_ORIGINS`, `EMAIL__RESEND_API_KEY`, `DB__DATABASE_URL`. Lives in `backend/.env` (template: `.env.example`).
- **No migrations.** `Base.metadata.create_all` runs on startup (`main.py` lifespan). Local dev defaults to SQLite (`aztec_list.db`); Docker uses PostgreSQL. Schema changes happen by editing models.

## Frontend (run from `frontend/`)

```bash
bun install
bun dev                  # dev server → http://localhost:3000
bun run build
bun run lint             # eslint   (lint:fix to autofix)
bun run format           # prettier (format:check to verify)
bun run test             # Jest — NOT `bun test` (that runs Bun's own runner, not Jest)
bun run test:e2e         # Playwright
bun audit                # dependency CVE check (CI gate)
```

Single Jest test: `bunx jest src/lib/__tests__/auth.test.ts -t "name"`.
Single Playwright test: `bunx playwright test tests/e2e/auth-login.spec.ts`.
Jest mocks router + fetch in `jest.setup.js`; use `renderWithProviders`/`mockFetch` from `src/test-utils.tsx`.

### Frontend architecture

- **Next.js App Router** (`src/app/`), React 19. No Next API routes — the frontend talks **directly** to the FastAPI backend.
- **Data layer:** `lib/api.ts` + `lib/messaging-api.ts` are typed `fetch` wrappers. Base URLs come from `lib/constants.ts` (`NEXT_PUBLIC_API_BASE_URL`, default `http://127.0.0.1:8000/api/v1`; `NEXT_PUBLIC_STATIC_BASE_URL` for uploaded images). Query params map 1:1 to FastAPI names (e.g. `q` → `search_text`).
- **Server state:** TanStack Query. `queryOptions/` holds per-domain query-option factories consumed by components.
- **Auth:** `contexts/AuthContext.tsx` for state; `lib/auth.ts` (`getAuthToken`) injects the JWT into API calls.
- **UI:** shadcn-style — `components/ui/` built on Radix + `cva` + `tailwind-merge`'s `cn` helper. Tailwind v4 (CSS-based config in `src/app/globals.css`). Prettier sorts classes via `prettier-plugin-tailwindcss`.
- Env config lives in `frontend/.env.local` (template: `.env.example`).

#### Frontend dependency constraints (don't regress these)

- **ESLint is pinned to `^9`.** Do not bump to v10 — `eslint-plugin-react`/`jsx-a11y`/`import` (pulled by `eslint-config-next`) have no ESLint 10 support yet and lint will crash.
- The `overrides` in `frontend/package.json` (`ws`, `postcss`) are **load-bearing security pins** that keep `bun audit` clean — don't remove without re-auditing.
- `bun.lock` is the only committed lockfile. Do not commit `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml`.

## Cross-cutting

- **Pre-commit** (config: `.pre-commit-config.yaml`): Ruff (backend), Prettier + ESLint (frontend, via `.pre-commit-hooks/` Python wrappers), gitleaks, and whitespace/EOL fixers. Install once from repo root: `uv tool install pre-commit && pre-commit install`. Run manually: `pre-commit run --all-files`.
- **CI/security** (`.github/workflows/`): `security-audit.yml` runs `pip-audit` (backend) and `bun audit` (frontend); `codeql.yml` (SAST); `gitleaks.yml` (secrets). A red `bun audit` blocks Dependabot PRs from merging — fix the advisory (often via a `package.json` override) rather than ignoring it.
- **Docker:** `docker-compose up --build` from repo root runs Postgres + backend + frontend; config via root `.env` (template `.env.example`).
