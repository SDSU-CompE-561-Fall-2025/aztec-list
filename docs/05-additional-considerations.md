# Part 5: Additional Considerations

## 1) Authentication

**Method:** JSON Web Tokens (JWT) using OAuth2 password flow. `/api/auth/login` authenticates credentials and returns an `access_token` with `token_type: bearer`; clients include it as `Authorization: Bearer <token>` on protected routes. Tokens are short‑lived (e.g., 60 minutes) and signed with HS256.

**Claims:** `sub` (user_id), `username`, `role` (`user|admin`), and `is_verified`. The `users.is_verified` flag is populated post‑email verification and can be required for state‑changing actions (e.g., creating listings or uploading images).

**Authorization rules:**
- Admin endpoints (`/api/admin/*`) require `role=admin`.
- On each request, middleware/dependencies check for active moderation against the caller: if an **AdminAction** of type `ban` exists and is unexpired (or permanent), effectful routes return **403** (`"Account banned"`). Time‑boxed bans rely on `expires_at`; listing moderation can also be enforced via `target_listing_id`.

**Password security:** Store `password_hash` only (bcrypt/passlib). Enforce minimum complexity at signup and lock out/slow down repeated failed logins (rate limiting described below).

---

## 2) Middleware

- **CORS:** Allow only approved front‑end origins; expose `Authorization`, support `GET, POST, PATCH, DELETE`, and enable preflight caching.
- **Rate limiting:** Per‑IP and per‑user sliding window (e.g., 100 req/15 min), with stricter limits on `/api/auth/*` to deter brute force. 429 responses include `Retry-After`.
- **Structured logging + request IDs:** Inject an `X-Request-ID` and log method, path, status, latency, and `user_id` (if authenticated).
- **Security headers:** HSTS (HTTPS only), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` (minimal), `X-Frame-Options: DENY`.
- **Validation & normalization:** Pydantic models enforce constraints (e.g., `min_price ≤ max_price`, `price ≥ 0`, valid `condition` enum). Invalid inputs return uniform errors (see §3).
- **File upload guardrails:** For listing images enforce count (1–10), type (`jpg/png/webp`), and size limits; reject non‑owners with **403**.
- **Pagination guardrails:** Enforce `limit` bounds (1–100) and cursor format for endpoints using `limit + cursor`.
- **Caching/compression:** Enable gzip; for cacheable `GET` responses (e.g., listings, listing detail, user listings) send `ETag/If-None-Match` or short `Cache-Control` hints to reduce bandwidth.
- **DB/session management:** Per‑request DB session with rollback on exceptions; close session in a `finally` block.
- **Admin policy checks:** Before mutating a listing or user, check for active `admin_actions` records that ban the actor or that removed the target listing.

---

## 3) Error Handling

**Shape:** Keep a consistent envelope and add a request correlation id when possible:
```json
{ "detail": "Human‑readable message", "request_id": "uuid-optional" }
```

**Status mapping (examples):**
- **400 Bad Request** – Parameter/domain validation (e.g., `max_price must be >= min_price`).
- **401 Unauthorized** – Missing/invalid token or bad login.
- **403 Forbidden** – Not resource owner, admin‑only route, or account banned.
- **404 Not Found** – Listing/user/image/action not found.
- **422 Unprocessable Entity** – Body/field validation errors at signup/login (note the draft typo “Unprocessable Identity”).
- **429 Too Many Requests** – Rate‑limit exceeded (includes `Retry-After`).
- **500 Internal Server Error** – Unexpected server errors; log stack trace internally and return a generic message.

For soft‑removed listings (if implemented), optionally return **410 Gone** from read endpoints; otherwise, use **404**.

---

## 4) Testing

**Manual/Exploratory:** Maintain a Postman collection covering happy paths and edge cases for all endpoints: listing search and detail, CRUD with ownership rules, image upload/thumbnail, auth, and the full admin action set (warning/strike/ban/listing_removal). Include environments for local/dev URLs and an “Admin” auth token.

**Automated:**
- **API tests (pytest + FastAPI TestClient):**
  - Auth: signup → login → authorized call; ensure 401 on missing token and 403 on admin routes without `role=admin`.
  - Listings: create/update/delete by owner; non‑owner forbidden; search filtering, sorting, and `limit + cursor` pagination semantics.
  - Images: upload types/count enforcement; set/clear thumbnail; deleting an image preserves thumbnail invariants.
  - Profiles: create/get/patch and picture upload flow.
  - Admin actions: create/list/get/delete; verify that active bans block mutations and that `expires_at` lifts bans automatically.
- **Fixtures:** Ephemeral DB (e.g., Postgres in Docker) migrated to the schema in Part 4; S3/local storage stub for images.
- **Coverage goals:** ≥90% on route handlers, validators, and policy checks.
- **Performance smoke:** Simple load test of `/api/listings` with realistic filters and pagination to catch N+1 queries and ensure indexes are effective.

**Release criteria:** All automated tests pass, Postman collection verified end‑to‑end, and no open critical defects in error handling or authorization.

---

### 5) E2E UI Testing (future)
**When to add:** once the web UI is stable enough to exercise login → listing CRUD → images → profile flows.

**Scope:**
- **Smoke (PR):** login, create listing, set thumbnail, edit+view listing, logout (<2m).
- **Regression (nightly):** filters/sorting/pagination, profile updates, admin actions, access control.

**Data & Auth:** seed known users/items; use programmatic login (hit `/api/auth/login`) and store the JWT to localStorage to skip UI auth.

**CI:** run smoke on every PR, full suite nightly; record video on failure only; parallelize if tests grow.

**Tooling:** Cypress **or** Playwright (tool‑agnostic for now). Use stable `data-test` selectors in the UI.
