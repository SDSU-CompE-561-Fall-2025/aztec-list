# syntax=docker/dockerfile:1

# ---- Builder: resolve and install production dependencies into a venv ----
# Pinned to 3.13 to match `requires-python`, CI (`uv python install 3.13`), and the
# resolved uv.lock. fastembed/onnxruntime wheels are not guaranteed on newer minors.
FROM python:3.13-slim AS builder

WORKDIR /app

# Build toolchain is only needed to compile any sdists during the install; it stays
# out of the runtime image below.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Install production dependencies only (no dev group: pytest/ruff/etc. are not needed
# to run the server). --frozen fails the build if uv.lock is out of sync with pyproject.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ---- Runtime: slim image carrying just the venv + application code ----
FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

# Run as a non-root user.
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

# Bring in the prebuilt virtualenv from the builder (no build tools in this layer).
COPY --from=builder /app/.venv /app/.venv

# Application code (migrations + scripts included; tests/local DB excluded via .dockerignore).
COPY . .

# Ensure the upload dir exists and the app user owns the tree.
RUN mkdir -p uploads && chown -R app:app /app

USER app

EXPOSE 8000

# Production server: no --reload. A single worker per container is intentional -- the
# WebSocket fan-out (active_connections) and the in-memory rate limiter keep state in
# this process, so running multiple workers/instances requires the deferred Redis
# pub/sub. Scale vertically for now; local dev re-enables --reload via docker-compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
