# US-033 — Retrieval Reranking — Cross-Encoder Step

## User Story

**As an** AI Engineer,  
**I want to** add a cross-encoder reranking step after hybrid retrieval that re-orders candidate evidence by relevance to the query using a reranking model,  
**So that** the evidence passed to synthesis is more precisely ranked than the initial RRF score alone can achieve, measurably improving top-k relevance on the golden evaluation dataset.

---

## Description

Reranking is FR-011 and was intentionally deferred from PI-1 (where the reranking hook was designed but the PassthroughReranker was used). This PI-2 story activates the reranking step with a real cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` via HuggingFace, or Cohere Rerank API). The `EvidenceItem.rerank_score` field (previously null) is now populated.

---

## Business Value

- Improves answer quality for queries where the initial vector + keyword merge ranks less-relevant chunks above more-relevant ones.
- Satisfies FR-011 acceptance check: "top-k relevance is measurably higher with reranking enabled than with the same retrieval step and reranking disabled."
- The deferred value from PI-1 is now realised: the corpus is large enough for reranking to show meaningful improvement.

---

## Acceptance Criteria

**Given** hybrid retrieval returns a set of candidate chunks (US-008),  
**When** the reranking step runs,  
**Then:**
- Each candidate chunk is scored by the cross-encoder model against the original query.
- Chunks are re-ordered by `rerank_score` (descending).
- `EvidenceItem.rerank_score` is populated for all returned chunks.
- Top-k relevance (RAGAS `context_precision`) on the golden evaluation dataset is ≥5pp higher with reranking enabled vs. the RRF-only baseline from PI-1.
- Reranking latency adds ≤500ms to median query latency (model loaded at service startup, not per-request).

---

## Functional Requirements

- FR-011 (Retrieval reranking).

---

## Non-Functional Requirements

- NFR-006 (Performance) — reranking latency ≤500ms median; model must be pre-loaded at startup.
- NFR-009 (Cost optimisation) — if using Cohere Rerank API, cost per query is logged as an OTel span attribute.

---

## Dependencies

- US-008 (Hybrid retrieval endpoint — the reranking hook designed here is now activated).
- US-021/US-023 (RAGAS evaluation harness — the top-k relevance improvement is verified here).
- US-028 (OTel tracing — reranking latency and cost captured as span attributes).

---

## Assumptions

- PI-2 uses a local cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`) as the default. The Cohere Rerank API is an option if latency requirements cannot be met with the local model.
- The model is loaded once at service startup and reused across requests.
- The number of candidates passed to the reranker = `top_k * 3` (more candidates → better reranking quality).
- `EvidenceItem.rerank_score` is already in the schema from US-013 (as a nullable float); this story populates it.

---

## Edge Cases

- **Reranker model fails to load at startup:** Service must refuse to start; log a clear error.
- **Reranker fails during a request:** Fall back to the RRF-ordered result (PassthroughReranker behaviour); log a warning; add `"reranking-unavailable"` to `guardrail_flags`.
- **All candidates have the same rerank score:** Return them in the original RRF order (no change).

---

## Technical Notes / Implementation Considerations

- **Implementation:** Replace `PassthroughReranker` with `CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")` in the dependency injection setup.
- **`CrossEncoderReranker.rerank(query, chunks)`:** Calls `model.predict([(query, chunk.content) for chunk in chunks])`; sorts by score; returns re-ordered chunks with `rerank_score` set.
- **Model startup:** Load in a `@asynccontextmanager` lifespan handler in `backend/app/main.py`.
- **OTel span attributes:** `retrieval.reranking_enabled=true`, `retrieval.reranking_model="cross-encoder/ms-marco-MiniLM-L-6-v2"`, `retrieval.reranking_latency_ms`.
- **Evaluation:** Run `scripts/run_evaluation.py --enable-reranking` vs. `--disable-reranking`; compare `context_precision` scores.

---

## Definition of Done

- [ ] `CrossEncoderReranker` implemented, replacing `PassthroughReranker`.
- [ ] Model loaded at startup; service refuses to start if model load fails.
- [ ] `EvidenceItem.rerank_score` populated for all returned chunks.
- [ ] Fallback to RRF order on reranker failure (with warning log).
- [ ] RAGAS `context_precision` improvement ≥5pp vs. baseline confirmed.
- [ ] Reranking latency ≤500ms median confirmed.
- [ ] OTel span attributes captured.
- [ ] CI evaluation gate updated with new threshold.
- [ ] Unit tests: reranking reorders correctly; fallback on failure.
- [ ] CI passes.

---

## Priority

**Medium** (Stretch in PI-2 per PI planning objectives).

## Estimated Effort

**M (Medium)** — ~2–4 days (CrossEncoderReranker, startup loading, fallback, evaluation comparison, tests).

## Related Epics / Features

- FEAT-18 (Retrieval reranking)
- FR-011
- NFR-006 (Performance)
