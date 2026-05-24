# AI Listing Features

AI features that build on the existing stack (local embeddings + Qdrant, the LLM provider
factory, and `AdminAction` moderation). They are opt-in, reuse the service layer, and degrade to
the pre-AI behaviour when `AI__ENABLED` is off. Plan and rationale: `docs/09-ai-roadmap.md`.

| Feature | What it does | Endpoint / surface |
| :--- | :--- | :--- |
| Auto-description (B1) | Drafts a listing description from the title and any details | `POST /ai/generate-description`; "Generate" button on the create/edit form |
| Similar listings (C1) | "More like this" on a listing page, ranked by meaning | `GET /listings/{id}/similar`; section on the listing detail page |
| Listing moderation + review queue (A1 + E3) | Flags borderline new listings for human review | create flow + admin "Flagged" tab (`GET /admin/flagged-listings`, `POST /admin/listings/{id}/approve`) |
| Image moderation (A2) | Flags listing photos with prohibited content via Claude vision | image upload flow; flags to the same review queue |

## Provider routing (hybrid)

`core/llm.py` exposes three builders so each task can use the right model:

- `get_chat_model()` - the shopping assistant (provider from `LLM__PROVIDER`).
- `get_assist_model()` - auto-description and moderation; provider from `LLM__ASSIST_PROVIDER`,
  falling back to `LLM__PROVIDER`. Set `LLM__ASSIST_PROVIDER=anthropic` for the recommended hybrid
  (Claude for these tasks, a local model for chat).
- `get_structured_model(schema)` - `get_assist_model()` with `.with_structured_output(schema)` for
  classification tasks (used by the moderation verdict). Returns validated Pydantic instances.

## Auto-description (B1)

`services/ai_listing_assist.py` builds a short prompt from the title plus any selected category,
condition, and free-text details, then calls `get_assist_model().ainvoke(...)`. The route
(`routes/ai.py`) requires auth, is rate-limited, returns 503 when AI is off, and fails to a
friendly 502 if the model is unavailable so the seller can still write their own copy. The prompt
forbids inventing facts and treats the seller's text as data, not instructions (prompt-injection
safe).

The frontend adds a "Generate" button beside the description label on both the create and edit
forms (`app/listings/create/page.tsx`, `app/listings/[listing_id]/edit/page.tsx`); it is disabled
until there is a title and fills the textarea with the result.

## Similar listings (C1)

`ListingService.get_similar` embeds the listing's own text and reuses `vector_store.search`,
excludes the listing itself, ranks by cosine score, and resolves to active rows. It returns an
empty list when AI is off or the search fails, so the page never breaks. No new infrastructure: it
rides the same index as semantic search. The `SimilarListings` component renders nothing when the
list is empty, so the detail page degrades cleanly.

## Listing moderation + review queue (A1 + E3)

Two layers run when a listing is created:

1. **Keyword filter (always on)** - `core/moderation.py` hard-blocks known violations with a 403,
   exactly as before.
2. **AI second-pass (opt-in)** - `moderation_service.review_new_listing` runs only when
   `AI__ENABLED` and `MODERATION__AI_REVIEW_ENABLED` are true, and is skipped for admins. It asks a
   structured-output model for a verdict and **fails open** (a model outage never blocks creation).

A borderline verdict does not reject the listing. Instead it is **flagged**: the listing is set
inactive and an `AdminActionType.FLAG` record (system-issued, `admin_id=None`) is written. Because
search and `get_by_ids` already filter on `is_active`, a flagged listing disappears from buyers
with no re-indexing needed.

The review queue reuses the admin surface:

- `GET /admin/flagged-listings` lists flagged listings with their reason.
- `POST /admin/listings/{id}/approve` clears the flags and reactivates the listing.
- Removal uses the existing `POST /admin/listings/{id}/remove` (strike + delete).

Enforcement is synchronous today (a fast model with fail-open), which adds a little latency to
creation when enabled; moving it to a background task is a future option.

## Image moderation (A2)

`moderation_service.review_listing_image` runs after a photo is saved (the `services/listing_image.py`
upload flow). It reads the stored image, sends it to Claude vision (`get_structured_vision_model`)
with a safety prompt, and on a violation flags the listing into the same review queue as A1
(deactivate + FLAG action). It is gated by `MODERATION__AI_IMAGE_REVIEW_ENABLED`, skips admins, runs
synchronously, and fails open (a vision outage never blocks the upload). Vision always uses
Anthropic, so it needs `LLM__ANTHROPIC_API_KEY` regardless of `LLM__ASSIST_PROVIDER`.

## Configuration

```bash
AI__ENABLED=true                       # master switch for all AI features
LLM__ASSIST_PROVIDER=anthropic         # hybrid: Claude for assist + moderation
LLM__ANTHROPIC_API_KEY=...             # required when assist/provider is anthropic
MODERATION__AI_REVIEW_ENABLED=true     # turn on the A1 second-pass (off by default)
```

With `AI__ENABLED=false` (default), `/ai/generate-description` returns 503, `/listings/{id}/similar`
returns `[]`, and listing moderation is keyword-only.

## Testing

- **Backend** (`tests/integration/`): `test_ai_listing_assist.py` (generate happy path, disabled,
  auth), `test_listing_similar.py` (ranking, self-exclusion, disabled, 404), `test_ai_moderation.py`
  (flag + deactivate, clean stays active, disabled skips, fail-open, queue list, approve, requires
  admin). LLMs use `GenericFakeChatModel`; retrieval uses the `memory_vector_store` fixture; both
  are toggled with `monkeypatch` on `settings`.
- **Frontend**: `src/lib/__tests__/api.test.ts` covers the typed clients with `mockFetch`.
