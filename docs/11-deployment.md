# Deployment

How to take Aztec List from the repo to a live environment. The app code is
production-shaped (security headers, health/readiness probes, Alembic migrations,
gated Sentry, prod config flags); this guide covers the hosting around it.

## Chosen stack

| Concern            | Service                          | Why |
| ------------------ | -------------------------------- | --- |
| Frontend           | Vercel                           | First-class Next.js host, env + preview deploys |
| Backend            | Fly.io                           | Always-on container, native WebSockets, persistent volume |
| Postgres           | Neon (or Fly Postgres)           | Managed; just a connection string |
| Vector store       | Qdrant Cloud (free tier)         | Managed Qdrant in server mode |
| Uploads + CDN      | Cloudflare R2                    | S3-compatible, zero egress, built-in CDN (issue #104) |
| LLM (prod)         | Anthropic (Claude Haiku)         | No model server to host; factory already supports it |
| Email              | Resend                           | Already integrated |
| Error tracking     | Sentry                           | Already integrated, gated on `SENTRY__DSN` |

Single backend instance for now: the WebSocket fan-out and in-memory rate limiter are
per-process. Horizontal scale (multiple machines/workers) needs Redis pub/sub, which is
deliberately deferred.

## 1. Backend on Fly.io

Config lives in `backend/fly.toml`. The production `backend/Dockerfile` is multi-stage,
runs as a non-root user, and serves with `uvicorn` (no `--reload`, single worker).

```bash
cd backend
fly launch --no-deploy                              # creates the app from fly.toml
fly volumes create uploads --size 3 --region sjc    # interim image storage (until R2)
```

Set secrets (injected as env vars at runtime; never commit these):

```bash
fly secrets set \
  JWT__SECRET_KEY="$(uv run python -c 'import secrets;print(secrets.token_urlsafe(32))')" \
  DB__DATABASE_URL="postgresql://...neon..." \
  CORS__ALLOWED_ORIGINS='["https://your-frontend.vercel.app"]' \
  CORS__FRONTEND_URL="https://your-frontend.vercel.app" \
  EMAIL__RESEND_API_KEY="re_..." \
  EMAIL__FROM_EMAIL="noreply@yourdomain.com" \
  AI__ENABLED="true" \
  VECTOR__QDRANT_URL="https://...qdrant-cloud..." \
  VECTOR__QDRANT_API_KEY="..." \
  LLM__ANTHROPIC_API_KEY="sk-ant-..." \
  SENTRY__DSN="https://...ingest.sentry.io/..."
```

```bash
fly deploy    # builds the image; release_command runs `alembic upgrade head` first
```

`[deploy].release_command` applies migrations before the new release takes traffic, so
the schema is always current. The `/health` check gates the rollout.

## 2. Postgres (Neon)

Create a Neon project, copy the pooled connection string into `DB__DATABASE_URL` (above).
Migrations run automatically on deploy via the release command; to run them by hand:
`fly ssh console -C "alembic upgrade head"`.

## 3. Vector store (Qdrant Cloud)

Create a free Qdrant Cloud cluster, then set `VECTOR__QDRANT_URL` + `VECTOR__QDRANT_API_KEY`.
After the first deploy, build the index once:

```bash
fly ssh console -C "python scripts/reindex_listings.py"
```

If you ship without AI, set `AI__ENABLED=false` and skip Qdrant entirely.

## 4. Uploads + CDN (Cloudflare R2) — issue #104

Until the R2 storage backend lands, uploads use the Fly volume mounted at `/app/uploads`
(works on a single machine; lost capacity to scale out). The R2 migration will:

- Add an S3-compatible storage backend selected by a `STORAGE__BACKEND` setting.
- Write/read images through the R2 bucket; serve them via the R2 public/CDN domain set in
  the frontend's `NEXT_PUBLIC_STATIC_BASE_URL`.
- Let you drop the `[mounts]` volume from `fly.toml` and run multiple machines.

R2 specifics (bucket, CORS for the upload path, signed URLs if private) are tracked in #104.

## 5. LLM (Anthropic)

`fly.toml` sets `LLM__PROVIDER=anthropic`; provide `LLM__ANTHROPIC_API_KEY` as a secret.
The Ollama container from `docker-compose.yml` is not deployed. To keep the local model for
chat while using Claude for moderation/auto-description, set `LLM__ASSIST_PROVIDER=anthropic`
and leave `LLM__PROVIDER=ollama` (hybrid) — but in a hosted, no-Ollama environment use
`anthropic` for both.

## 6. Frontend on Vercel

Import the repo, set the project root to `frontend/`, and configure env:

```
NEXT_PUBLIC_API_BASE_URL=https://aztec-list-backend.fly.dev/api/v1
NEXT_PUBLIC_STATIC_BASE_URL=https://<r2-public-domain>   # or the Fly URL until R2 lands
```

Vercel runs `bun install` + `bun run build` automatically. After the frontend domain is
known, update the backend's `CORS__ALLOWED_ORIGINS` / `CORS__FRONTEND_URL` secrets to match.

## Pre-launch checklist

The full per-variable list is in `backend/.env.example` under "PRODUCTION OVERRIDES
CHECKLIST". The essentials:

- [ ] `APP__ENVIRONMENT=production` (disables `/docs`, `/redoc`, `/openapi.json`)
- [ ] `JWT__SECRET_KEY` rotated to a fresh 32+ char random value
- [ ] `DB__DATABASE_URL` points at managed Postgres
- [ ] `CORS__ALLOWED_ORIGINS` is the exact frontend origin (never `*` with credentials)
- [ ] `LOGGING__USE_JSON=true`, `TEST__TEST_MODE=false`, `RATE_LIMIT__ENABLED=true`
- [ ] `SENTRY__DSN` set (recommended)
- [ ] `alembic upgrade head` has run against the prod database (automatic via deploy)
- [ ] `/health` returns 200 and `/ready` reflects DB + Qdrant
