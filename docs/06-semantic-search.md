# Semantic Search (AI)

AI-powered listing search that ranks by **meaning**, not just keyword overlap — so
"something I can drive" surfaces the Porsche and the driving game, and "cologne that
smells good" finds the fragrances even though none of them contain the word "cologne".

It is **opt-in** (`AI__ENABLED=true`) and sits alongside the existing keyword (SQL `ILIKE`)
search. Users toggle it with the **"Smart search (AI)"** switch on the listings page.

## How it works

| Layer | File | Role |
| :--- | :--- | :--- |
| Embeddings | `services/embeddings.py` | Local [fastembed](https://github.com/qdrant/fastembed) model turns text into a vector. No API key, runs offline; the model is lazy-loaded on first use. |
| Vector store | `services/vector_store.py` | [Qdrant](https://qdrant.tech) stores vectors + a small payload (category, condition, price, seller, is_active) and runs filtered similarity search. |
| Search wiring | `services/listing.py` | `ListingService.get_filtered` branches to the vector path when `semantic=true` **and** `search_text` is set **and** AI is enabled; otherwise the keyword path is untouched. Falls back to keyword search on any error. |
| Index lifecycle | `services/listing.py` | Create/update/delete upsert/remove the listing's vector (best-effort; failures are logged, never block the write). |
| Backfill | `scripts/reindex_listings.py` | Clean rebuild of the vector index from the database. |

**Query flow:** `GET /listings?search_text=...&semantic=true` → embed query → Qdrant
similarity search (with structural filters) → apply the relevance cutoff → resolve the
surviving IDs back to live DB rows (drops stale vectors) → return ranked listings, each
carrying a `relevance_score`.

Embeddings are local and SQLite-friendly; only the vector store is separate. Locally it
runs as an **embedded on-disk Qdrant** (no extra process); in Docker it points at a Qdrant
container via `VECTOR__QDRANT_URL`.

## Configuration

All nested under the `__` env delimiter (see `backend/.env.example`):

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AI__ENABLED` | `false` | Master switch. Off = keyword search only, no model loaded. |
| `EMBEDDING__MODEL` | `BAAI/bge-small-en-v1.5` | fastembed model (see benchmark below). |
| `VECTOR__QDRANT_URL` | `""` | Qdrant server URL. Empty → embedded on-disk at `VECTOR__PATH`. |
| `VECTOR__PATH` | `./qdrant_data` | On-disk path for embedded Qdrant. |
| `VECTOR__COLLECTION` | `listings` | Collection name. |
| `VECTOR__SCORE_FLOOR` | `0.40` | Absolute min cosine; below it, the query matches nothing. |
| `VECTOR__RELATIVE_MARGIN` | `0.05` | Keep listings within this cosine of the best hit. |

## Relevance cutoff (two layers)

Pure k-NN returns *everything* ranked, so without a cutoff a vague query returned the whole
catalogue. Two layers trim it:

1. **Absolute floor** (`SCORE_FLOOR`) — if even the best hit is below it, return nothing.
2. **Relative margin** (`RELATIVE_MARGIN`) — keep only listings within this cosine of the
   top hit.

The relative margin matters because cosine scores **drift per query**. A fixed threshold is
brittle: too high nukes valid-but-vague queries, too low keeps junk. Anchoring to the best
hit adapts automatically. Worked example (real `bge-small` scores, "something I can drive"):

```
Porsche .612  GTA .590  drugs .566  Stapler .558  Airpods .537  ...  Squidward .428
top = .612, margin = .05  ->  keep >= .562  ->  Porsche, GTA, drugs   (tail dropped)
```

**Tuning:** results too broad → lower `RELATIVE_MARGIN` (e.g. `0.04`); valid matches getting
cut → raise toward `0.07`. `0.05` was calibrated against real listings (below).

## Benchmark findings

These drove the design. Measured on the **real listing data** (19 listings) with realistic
buyer queries — a small, indicative eval, not a formal benchmark, but enough to overturn two
"textbook" assumptions.

### 1. Model: `bge-small` is the sweet spot — bigger is not better

5 fastembed models, 12 queries (rank@1 = top result relevant; MRR / Recall@3 over all):

| Model | dim | size | rank@1 | MRR | Recall@3 |
| :--- | :-- | :-- | :-- | :-- | :-- |
| **BAAI/bge-small-en-v1.5** (default) | 384 | 67 MB | **11/12** | **0.958** | 0.944 |
| thenlper/gte-base | 768 | 440 MB | 11/12 | 0.944 | 0.944 |
| BAAI/bge-base-en-v1.5 | 768 | 210 MB | 10/12 | 0.917 | 0.944 |
| snowflake/arctic-embed-s | 384 | 130 MB | 10/12 | 0.917 | 0.903 |
| mixedbread/mxbai-embed-large-v1 | 1024 | 640 MB | 10/12 | 0.903 | 0.944 |

The 67 MB model ties or beats everything up to 10× its size. Larger MTEB-leaderboard models
(mxbai, gte) did **not** separate this short-title catalogue better, so the default stays
`bge-small`: tiny, fast, 384-dim (cheap storage), offline.

### 2. Hybrid (BM25) would hurt here — dense already wins

Conventional advice is "add BM25 + fuse with RRF" for short text. Measured on this data it
**regressed**, so it was **not** adopted:

| Method | Semantic queries (n=10) rank@1 / MRR | Lexical/brand queries (n=6) rank@1 / MRR |
| :--- | :--- | :--- |
| **dense (bge-small)** | **9/10 / 0.950** | **6/6 / 1.000** |
| bm25 | 5/10 / 0.596 | 6/6 / 1.000 |
| hybrid (RRF) | 6/10 / 0.739 | 6/6 / 1.000 |

On semantic queries the title rarely shares words with the query, so BM25 scores poorly and
drags hybrid below pure dense. On brand/keyword queries ("bape hoodie", "labubu", "gta v")
dense is already perfect because the embedding captures those tokens. Hybrid only makes sense
in the abstract; on this corpus it adds nothing and costs precision. (Worth revisiting if
descriptions get much longer or the catalogue grows a lot.)

### 3. Negative results (also measured, also skipped)

- **Query instruction prefix** ("Represent this sentence…") — *slightly hurt* `bge-v1.5`,
  which dropped the instruction requirement. fastembed applies none anyway.
- **Doc enrichment with labelled fields** ("Category: X. Condition: Y. …") — *hurt*; the
  shared boilerplate tokens dilute the vector.

### Conclusion

The retrieval bottleneck was never ranking quality (~0.95 MRR already) — it was the
**cutoff**. Keep `bge-small`, invest in the threshold. Reranking is moot at this MRR.

## Operations

**Backfill / repair the index** (e.g. after enabling AI on an existing DB, or to clear
drift). The embedded Qdrant is single-process, so stop the dev server first:

```bash
# from backend/, with the dev server stopped
uv run python scripts/reindex_listings.py     # drops + recreates the collection, re-embeds all
```

**Dual-store drift:** the DB and Qdrant are two stores. The lifecycle hooks keep them in sync
**while AI is enabled**; deletes/deactivations that happen while AI is *off* leave orphan
vectors behind. Searches drop orphans at query time (IDs are re-resolved to live active rows,
and the result count reflects only those), and `reindex_listings.py` clears them for good.

**Embedded vs server:** embedded on-disk Qdrant is single-process — fine for a single dev
worker. For multiple workers, or to run the reindex while the server is up, run the Qdrant
container and set `VECTOR__QDRANT_URL`.

## Limitations & future work

- **Vague queries on short titles** cluster tightly (`bge-small` scored 0.43–0.61 across the
  whole catalogue for "something I can drive"). The cutoff handles it, but separation is
  inherently soft — a known trait of small embedders on short text.
- **Content artifacts**, not retrieval bugs: a listing literally titled "drugs" scores high
  for many queries. That is a moderation concern (planned LLM moderation), not tuning.
- **If the catalogue/descriptions grow:** re-benchmark; hybrid (BM25 + dense) and a
  cross-encoder reranker (`ms-marco-MiniLM`, ~80 MB) become worth their cost as documents
  lengthen.
- **Pagination** is over the top-N most-relevant candidates, not the full catalogue.

## Testing

- `tests/unit/test_vector_store.py` — Qdrant logic against an in-memory instance + a
  deterministic fake embedder (offline, no model download).
- `tests/integration/test_semantic_search.py` — end-to-end wiring: ordering, relative cutoff,
  orphan-vector exclusion, and keyword fallback when AI is off.
- `tests/unit/test_embeddings.py` — real-model smoke test, marked `slow` (downloads the model;
  skip with `-m "not slow"`).
