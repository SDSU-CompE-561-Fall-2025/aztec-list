# AI Feature Roadmap

A focused plan for expanding AI across the marketplace beyond the three features already shipped
(semantic search, the shopping assistant, the MCP server). The scope is deliberately lean: a small
set of essential features that reuse the existing AI stack, with the heavier and more sensitive
ideas explicitly deferred.

Every AI feature stays optional and degrades cleanly. It sits behind `AI__ENABLED` and the per-call
try/except fallback already used by `_index_listing` (`services/listing.py:233`), so the app
behaves exactly as it does today when AI is off or a provider is down.

## Why

- **Moderation is keyword and regex only** (`core/moderation.py`): text-only, listings-only, and it
  misses context, intent, and novel evasion.
- **Sellers get no authoring help.** Title, description, and category are all manual
  (`app/listings/create/page.tsx`).
- **Support tickets get no triage.** `services/support_ticket.py:86` stores every ticket as `OPEN`
  with no category or priority.
- Discovery (semantic search + assistant) is the mature area and is the template for the rest.

## Scope

**In (this plan):**

| ID | Feature | Phase |
| :--- | :--- | :--- |
| A1 | AI listing moderation | 1 (shipped) |
| B1 | Auto-description | 1 (shipped) |
| C1 | Similar listings | 1 (shipped) |
| E3 | Admin review queue (lean) | 1 (shipped) |
| A2 | Image moderation | 2 (shipped) |
| E1 | Support ticket triage | 2 |

**Deferred / out of scope:**

- **A3 message moderation: dropped.** Message safety will be handled by user reporting, a separate
  non-AI plan written later. No automated system should read private 1:1 messages, so this stays
  out of the AI roadmap entirely.
- **B2 auto-categorize: dropped** during the Phase 1 build. The category dropdown is already
  low-friction, so a one-click suggestion was marginal value for an extra button and LLM call. It
  could return later folded into the auto-description action.
- **E2 support suggested answers: deferred** until a curated help/FAQ knowledge base exists to
  ground on. The hard part is content, not code.
- **Broader landscape, future:** visual search, near-duplicate/fraud signals, price and title
  assist, and in-thread messaging AI. Intentionally excluded to keep this set essential.

## Provider strategy: hybrid

Route each task to the cheapest model that does the job well. Embeddings stay local; Claude handles
quality-sensitive generation and moderation reasoning; local Ollama is the offline fallback.

| Task | Model | Why |
| :--- | :--- | :--- |
| Text embeddings + similar listings (C1) | local fastembed `bge-small` | offline, free, already tuned (`docs/06`) |
| Vector lookups (C1) | none (vector search only) | deterministic, no LLM cost |
| Listing moderation (A1), triage (E1) | Claude Haiku, structured output | reliable JSON, cheap per call |
| Auto-description (B1) | Claude Haiku | quality matters |
| Image moderation (A2, Phase 2) | Claude Haiku/Sonnet vision | native multimodal, and keeps the container slim (no local llava download) |
| Offline fallback for any LLM task | local Ollama | when `AI__ENABLED` but no API key |

**Foundation change this requires:** `core/llm.py` currently picks one provider globally via
`settings.llm.provider`. Hybrid needs the factory to choose a provider per task so Anthropic and
Ollama can coexist (see Phase 0).

## Phase 0: shared foundation

Small, low-risk, copies existing conventions. Unlocks Phase 1. (The vision factory is not needed
here; it lands with A2 in Phase 2.)

- **`core/llm.py`**: add `get_structured_model(schema)` (LangChain `.with_structured_output()`,
  works on both providers) for A1 (and later E1); and let the factory pick a provider per task (a "fast"
  vs "fallback" model) so Claude and Ollama coexist. Keep the lazy-import + graceful-fallback style
  already in the file.
- **`core/settings.py`**: extend `LLMSettings` / `AISettings` with the fast model, per-feature
  flags, and a moderation mode (block vs flag), using the existing `__`-nested pattern.
- **New services** (`services/ai_moderation.py`, `services/ai_listing_assist.py`): each gated by
  `settings.ai.enabled` and wrapped in try/except that degrades to current behavior, mirroring
  `_index_listing` (`services/listing.py:233`).
- **Frontend**: new `lib/ai-api.ts` functions and TanStack mutation hooks mirroring `useAIChat`;
  "Generate" / "Suggest" buttons in `app/listings/create/page.tsx` and
  `app/listings/[listing_id]/edit/page.tsx`.

## Phase 1: seller assist + moderation core

All reuse-only, no vision, no message scanning. This is one cohesive text-and-vector build.

| Feature | Hook / surface | Reuse | Model |
| :--- | :--- | :--- | :--- |
| A1 listing moderation | wrap `content_moderator.check_content` at `services/moderation.py:52` | existing keyword check + LLM | Claude Haiku (structured) |
| B1 auto-description | new endpoint in `routes/ai.py`; button on create/edit form | `get_assist_model` | Claude Haiku |
| C1 similar listings | new endpoint over `vector_store.search` + `ListingFilter` (exclude self, relative margin); listing detail page | vector store, 0 new | none |
| E3 review queue (lean) | reuse `AdminAction` (`services/admin.py`); admin list filtered to flagged | existing admin infra | none |

**Enforcement model (A1 + E3):** keep the keyword check as an instant hard-block (high precision,
403 at `routes/listings.py`). The AI pass is a second layer: clear violations also block, but
borderline content is flagged rather than rejected. A flag sets the listing inactive
(`is_active=False`) and records an `AdminAction` reason, and the admin view filters to flagged
listings for review. This plugs into the existing STRIKE/BAN flow, it does not replace it.

## Phase 2: vision + support

| Feature | Hook / surface | Notes |
| :--- | :--- | :--- |
| A2 image moderation | `services/listing_image.py` upload / `core/storage.py` `save_upload_file` | Adds `get_vision_model()` to the factory. Runs async, fails open, flags to the E3 queue. Closes the v1 gap where a clean-text listing can carry a bad photo. |
| E1 ticket triage | `services/support_ticket.py:86` | New priority field/enum on the ticket; Claude Haiku structured output for category + priority. |

## Cross-cutting principles

- **Never block the user path.** Moderation and generation run async or as opt-in buttons, never
  inside the synchronous upload path. A1 uses a fast model with a timeout that fails open to the
  keyword block.
- **Prompt injection.** Extend the "treat listing text as untrusted data, never instructions" rule
  already in `services/rag.py` to every new LLM call. Listings and tickets are user-controlled.
- **Security gates.** Wrap any logged user text in `sanitize_log()` (`core/logging_safe.py`). Run
  `pip-audit` and `bun audit` after adding any dependency (Claude needs `langchain-anthropic`;
  vision packages land in Phase 2).

## Testing approach

- **Backend**: reuse `GenericFakeChatModel` for the LLM and the `memory_vector_store` fixture for
  retrieval; `monkeypatch` `settings.ai.enabled` on and off. Cover the violation path, the clean
  path, and the AI-disabled fallback for each feature (model after
  `tests/integration/test_ai_assistant.py` and `tests/unit/test_listing_moderation.py`).
- **Frontend**: `mockFetch` + `renderWithProviders` from `src/test-utils.tsx`; test hook state
  transitions (loading, success, error) as in `src/hooks/__tests__/useAIChat.test.ts`.

## Verification (end to end)

Run the backend with `AI__ENABLED=true` and the hybrid provider configured, then:

- Create a borderline listing and confirm it lands flagged/inactive in the admin view (A1 + E3),
  while a clean listing publishes normally and an obvious-violation keyword still hard-blocks.
- On the create form, click "Generate" and confirm the description populates, and "Suggest" sets a
  category (B1, B2).
- Open a listing and confirm related items appear (C1).
- Toggle `AI__ENABLED=false` and confirm every path falls back to today's behavior.

## Docs

Each shipped feature gets its own guide in `docs/`, matching the format of `06-semantic-search.md`,
`07-ai-assistant.md`, and `08-mcp-server.md` (how it works, configuration, design decisions,
limitations, testing).
