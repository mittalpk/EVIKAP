# US-008 — Hybrid Semantic + Keyword Retrieval Endpoint

## User Story

**As a** Developer / AI Engineer,  
**I want to** implement the `POST /api/v1/knowledge/query` endpoint to perform hybrid retrieval — combining pgvector cosine similarity search with keyword/BM25 ranking, merging and deduplicating results, then returning the top-k ranked evidence chunks with citations — so that the agent orchestration tier receives semantically relevant, source-attributed evidence for synthesis.

---

## Description

This story replaces the existing `GitHubSearchSubsystem` keyword-only query path with a real hybrid retrieval pipeline. The endpoint:
1. Generates a query embedding from the natural-language query.
2. Performs vector similarity search (pgvector) against the `Chunk.embedding` column.
3. Performs keyword search (BM25 or PostgreSQL full-text search `tsvector`) against `Chunk.content`.
4. Merges results using Reciprocal Rank Fusion (RRF) or a weighted score merge.
5. Applies permission filtering (requester_identity vs `Chunk.permissions_ref`) — see US-014.
6. Returns the top-k chunks as structured `EvidenceItem` objects with `relevance_score` and `source_url`.

Note: reranking (US-033 / FEAT-18) is a PI-2 addition that slots in after step 4; the endpoint must be designed with a pluggable reranking hook even if it is not activated in PI-1.

---

## Business Value

- Replaces the single largest quality gap in the current platform: keyword retrieval mis-branded as semantic search.
- Directly enables FR-002 acceptance check: "a query phrased differently from the source document's wording retrieves the correct source in top-k."
- Provides the evidence pipeline that US-012 (citations) and US-021 (RAGAS evaluation) depend on.

---

## Acceptance Criteria

**Given** at least one `Source` has been ingested (US-006 or US-007 complete) and chunks with embeddings exist in the database,  
**When** `POST /api/v1/knowledge/query` is called with `{"query": "<natural language question>", "requester_identity": "<identity>", "top_k": 5}`,  
**Then:**
- A query embedding is generated and a pgvector similarity search is performed.
- A keyword search is performed over `Chunk.content` using PostgreSQL full-text search.
- Results from both searches are merged and deduplicated using RRF.
- Permission filtering is applied (only chunks the requester has access to are returned) — placeholder implementation acceptable if US-014 is not yet complete; must not be skippable.
- The response is a typed JSON object: `{"evidence": [{"chunk_id": ..., "content": ..., "source_url": ..., "relevance_score": ..., "source_id": ...}], "trace_id": ...}`.
- A query phrased differently from the source wording but semantically equivalent retrieves the correct chunk in top-k (manual spot-check against the pilot corpus).
- A reranking hook is present in the code path (no-op / passthrough in PI-1, activatable in PI-2).
- Endpoint has unit tests covering: embedding call, vector search, keyword search, merge logic, permission filter, response schema.

---

## Functional Requirements

- FR-002 (Cross-source semantic retrieval) — this is the core implementation.
- FR-006 (Permission-aware retrieval) — permission filter applied at query time.
- FR-011 (Retrieval reranking) — hook present, activated in PI-2.

---

## Non-Functional Requirements

- NFR-006 (Performance) — median query latency target: ≤2 seconds for top-5 results on the pilot corpus (≤50K chunks). Measure and log per-query latency.
- NFR-002 (Security) — `requester_identity` validated against a trusted source (JWT claim or internal service key); not caller-supplied free text.
- NFR-007 (Observability) — `trace_id` returned in every response; per-query latency and embedding model token cost logged.

---

## Dependencies

- US-005 complete (live database with pgvector).
- US-006 and/or US-007 complete (at least one source ingested with embeddings).
- US-014 (permission-aware retrieval) — can be a placeholder filter in PI-1 if US-014 is in parallel; must not be absent.

---

## Assumptions

- PostgreSQL full-text search (`tsvector` + `tsquery`) is sufficient for the keyword leg of hybrid retrieval at pilot corpus size; BM25 via `pg_bm25` extension is a PI-2 upgrade if full-text search quality is insufficient.
- RRF with default parameters (k=60) is a reasonable merge strategy for MVP; tunable post-measurement.
- The embedding dimension (768 for `text-embedding-004`) matches the `pgvector` column type established in the Alembic migration.
- `top_k` default is 5; configurable per-call up to 20.

---

## Edge Cases

- **No chunks in database (empty corpus):** Return `{"evidence": [], "trace_id": "..."}` with a `X-VigilRAG-Warning: corpus-empty` header.
- **Embedding model API call fails:** Return HTTP 503 with a structured error; do not fall back silently to keyword-only (would break FR-002 acceptance check without signaling the degradation).
- **Permission filter removes all results:** Return `{"evidence": [], "trace_id": "..."}` with `X-VigilRAG-Info: all-results-filtered-by-permission`. Do not expose that results exist but were filtered.
- **`top_k` > actual number of eligible chunks:** Return all eligible chunks; do not error.
- **Query embedding identical to a known prompt-injection payload:** Handled upstream by Guardrails (US-024); the retrieval endpoint itself does not do injection detection.

---

## Technical Notes / Implementation Considerations

- **Router location:** `backend/app/routers/knowledge.py` — extend or replace the existing `POST /api/v1/knowledge/query` handler.
- **Vector search query:** `SELECT *, 1 - (embedding <=> $query_embedding) AS similarity FROM chunks WHERE source_id IN (...) ORDER BY similarity DESC LIMIT top_k * 2` (fetch 2x for merge headroom).
- **Keyword search query:** `SELECT *, ts_rank(to_tsvector('english', content), plainto_tsquery('english', $query)) AS rank FROM chunks WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $query) LIMIT top_k * 2`.
- **RRF merge:** `score_rrf = 1/(k + rank_vector) + 1/(k + rank_keyword)` where k=60; sort by `score_rrf DESC`, take top_k.
- **Reranking hook:** `chunks = reranker.rerank(query, chunks)` — `reranker` is injected as a dependency; default is `PassthroughReranker` (returns chunks unchanged) in PI-1.
- **`EvidenceItem` schema:** Add to `backend/app/models.py` or a separate `schemas.py`; include `chunk_id`, `content`, `source_url`, `relevance_score`, `rerank_score` (null if not reranked), `source_id`.

---

## Definition of Done

- [ ] `POST /api/v1/knowledge/query` implements hybrid retrieval (vector + keyword + RRF merge).
- [ ] Permission filter applied (placeholder acceptable if US-014 not yet merged).
- [ ] Reranking hook present (PassthroughReranker default).
- [ ] Response schema matches the typed `EvidenceItem` structure with `trace_id`.
- [ ] Unit tests cover all major code paths (mocked DB, mocked embedding API).
- [ ] Manual spot-check: a semantically-equivalent but differently-worded query retrieves the correct chunk in top-5.
- [ ] Per-query latency logged; median ≤2s confirmed on pilot corpus.
- [ ] CI passes with new tests.
- [ ] Old `GitHubSearchSubsystem` keyword-only path disabled or removed.

---

## Priority

**High** — Core retrieval capability; blocks US-009, US-011, US-012, US-021.

## Estimated Effort

**L (Large)** — ~5–8 days (vector search, keyword search, RRF, permission filter, response schema, unit tests).

## Related Epics / Features

- FEAT-02 (Hybrid semantic + keyword retrieval)
- FEAT-06 (Permission-aware retrieval — filter applied here)
- FEAT-11 (Platform hardening — latency and observability logging)
- FEAT-18 (Retrieval reranking — hook designed here, activated in PI-2)
