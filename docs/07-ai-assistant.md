# AI Shopping Assistant (RAG)

A conversational assistant that answers shopping questions grounded in real listings.
"something to listen to music" returns a streamed recommendation that cites the actual
Airpods and Headset listings, with clickable links. It is opt-in (`AI__ENABLED=true` plus a
configured LLM) and reuses the Phase 1 semantic search index (see
[06-semantic-search.md](06-semantic-search.md)).

## How it works

| Layer | File | Role |
| :--- | :--- | :--- |
| LLM provider | `core/llm.py` | `get_chat_model()` returns a LangChain chat model for the configured provider (Ollama by default, Anthropic optional), imported lazily. `expand_query()` rewrites a vague query into product keywords. |
| RAG graph | `services/rag.py` | A small [LangGraph](https://langchain-ai.github.io/langgraph) `retrieve -> generate` graph: retrieve relevant listings via the vector store, ground the prompt in them, generate the answer. |
| Orchestration | `services/ai_assistant.py` | Drives a turn: persists the user message, runs the graph, streams answer tokens as SSE, then persists the assistant message with the listings it cited. |
| Data | `models/ai_conversation.py`, `repository/ai_conversation.py`, `schemas/ai.py` | `AIConversation` + `AIMessage` (role, content, JSON `sources`), per-user, with history. |
| API | `routes/ai.py` | `POST /ai/chat` (SSE), `GET /ai/conversations`, `GET /ai/conversations/{id}`. Auth + rate limited + gated on `AI__ENABLED`. |
| Frontend | `lib/ai-api.ts`, `hooks/useAIChat.ts`, `components/ai/AssistantSheet.tsx` | A floating "Ask AI" button opens a slide-in chat: streamed markdown reply, cited listings linked inline and shown as chips. |

**Streaming:** LangGraph is streamed with `stream_mode=["updates", "messages"]`. The `messages`
mode yields the generation tokens (emitted as SSE `token` events); the assistant message and
its sources are persisted after the stream completes. SSE event types: `start`, `token`,
`sources`, `done`, `error`.

## Configuration

LLM settings (nested `__` env vars, see `backend/.env.example`):

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AI__ENABLED` | `false` | Master switch (shared with semantic search). |
| `LLM__PROVIDER` | `ollama` | `ollama` (local, free) or `anthropic` (Claude). |
| `LLM__OLLAMA_MODEL` | `qwen2.5:7b` | Local model. `ollama serve` + `ollama pull qwen2.5:7b`. |
| `LLM__OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL. |
| `LLM__ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Used when provider is anthropic. |
| `LLM__ANTHROPIC_API_KEY` | `""` | Required when provider is anthropic. |
| `LLM__TEMPERATURE` | `0.2` | Lower is steadier. |
| `LLM__RETRIEVAL_K` | `6` | Listings used to ground each answer. |
| `LLM__EXPAND_QUERIES` | `true` | LLM keyword expansion before embedding (falls back to the raw query if the LLM is down). |

## Retrieval and grounding

The assistant grounds on a generous candidate set and lets the LLM decide what to recommend:

1. **Expand** the user's message into keywords (bridges vague phrasing to terse titles).
2. **Retrieve** the top-k by embedding similarity, then **resolve** to live active rows (drops
   deleted or orphan vectors) and trim to those within `relative_margin` of the best hit.
3. **Generate** grounded only in those listings.
4. **Cite** only the listings the answer actually names (matched by exact title), so the
   sources reflect what was recommended, not the whole candidate pool.

Multi-turn follow-ups ("any others?") retrieve using the previous turn plus the current
message, so they stay on topic.

## Design decisions (and what was tried)

These came out of heavy iteration; they are the interesting part for a reviewer.

- **The generation model is the quality ceiling.** `qwen2.5:3b` conflated listings (invented an
  "Airpod Pro" by merging two), recommended unrelated items (dumbbells for music), and ordered
  poorly. `qwen2.5:7b` (or Claude) fixed these with no other change. The default is `qwen2.5:7b`.
- **Let the LLM judge relevance, not cosine.** On short titles the embedder cannot separate
  "Headset" from "Dumbbells" for a music query (measured in 06-semantic-search.md). So grounding
  is generous and the LLM filters, and only recommended listings are cited.
- **Query expansion** (natural language to product keywords) is the lever that made vague
  queries work, for both search and the assistant.
- **Prompt rules** that mattered: recommend only from the listings, never invent items or
  brands; lead with the best fit; refer to listings by exact title, never by number or position;
  do not merge or rename listings; skip listings that do not fit. Enum values are humanized
  (`like_new` becomes "like new") before the model sees them.
- **Rejected:** a cross-encoder reranker (out of distribution on short product titles, ranked a
  stapler first for "music"), an LLM category filter for search (reverted as too coarse for the
  benefit), and larger embedding models (no measured gain). See 06-semantic-search.md.

## Limitations and future work

- Quality depends on the generation model. Small local models can still wander; use
  `qwen2.5:7b` or larger, or `LLM__PROVIDER=anthropic`, for reliable results.
- Conversation history is persisted per user and exposed via the API, but the UI shows only the
  current session (no history browser yet).
- Query expansion adds one LLM call per smart search. It falls back to the raw query if the LLM
  is unavailable, so search never hard-depends on it.

## Testing

- `tests/unit/test_llm.py` - query expansion (mocked chat model).
- `tests/unit/test_rag.py` - retrieval and prompt grounding helpers.
- `tests/integration/test_ai_assistant.py` - the SSE chat flow and conversation endpoints, using
  a fake chat model (`GenericFakeChatModel`) and an in-memory vector store, so the suite is fully
  offline and deterministic.
