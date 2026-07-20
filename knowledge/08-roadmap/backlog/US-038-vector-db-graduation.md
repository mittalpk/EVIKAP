# US-038 — Vector Database Graduation Evaluation & Migration

## User Story

**As a** Platform Engineer / AI Engineer,  
**I want to** evaluate whether the trigger criteria for graduating from pgvector to a dedicated vector database (Qdrant or Weaviate) have been met, and if so, plan and execute the migration,  
**So that** the platform's retrieval index scales gracefully beyond the point where pgvector performance degrades.

---

## Description

Unlike other features, FEAT-20 is not assigned to a fixed PI — it is triggered by criteria in [Technology Architecture §6a](../../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path). This story is the evaluation and (conditional) migration process. If ≥2 trigger signals are met, a PI-level spike is opened regardless of which PI is in flight. If signals are not met, the story closes with a documented non-migration decision.

---

## Business Value

- Ensures the platform scales beyond pilot to enterprise scale (NFR-001) without an emergency architectural rework.
- Prevents premature migration: graduation only happens when evidence supports it, not on a fixed schedule.
- The explicit trigger criteria mean the decision is data-driven, not technology-driven.

---

## Acceptance Criteria

**Given** the current retrieval corpus size, query latency measurements, and operational load metrics,  
**When** the trigger evaluation is run (at any PI boundary or when a trigger signal is detected),  
**Then:**
- The trigger criteria from Technology Architecture §6a are evaluated against current measurements:
  - [ ] Corpus size > 500K chunks (pgvector full-scan latency > 500ms at p90)
  - [ ] Query latency p90 > 2× the target (NFR-006)
  - [ ] Filtering complexity requires ANN index that pgvector doesn't support efficiently
  - [ ] Operational load (index build time) > acceptable threshold
- If ≥2 signals are met: a migration plan is produced (target vector DB selected, migration steps documented, data backfill plan agreed).
- If < 2 signals are met: a "no migration" decision record is produced, documenting the measurement values and the next evaluation date.
- If migration proceeds: pgvector data is migrated to the target vector DB; the retrieval endpoint is updated to use the new backend; latency measurements confirm improvement; zero data loss verified.

---

## Functional Requirements

- FR-002 (Cross-source semantic retrieval — the retrieval index backend may change; the retrieval contract does not).

---

## Non-Functional Requirements

- NFR-001 (Scalability) — migration is the mechanism for scaling beyond pgvector's limits.
- NFR-010 (Maintainability) — the retrieval endpoint's vector search is encapsulated behind an interface (`VectorSearchBackend`); swapping the backend is a configuration change, not an application code change.

---

## Dependencies

- US-008 (Hybrid retrieval endpoint — the `VectorSearchBackend` interface must be designed for replaceability; this should be done in US-008 if not already present).
- US-028 (OTel tracing — latency measurements used as trigger signals come from OTel).
- Technology Architecture §6a trigger criteria document.

---

## Assumptions

- The trigger evaluation is performed at each PI boundary by the AI engineering team as a standard PI planning activity.
- Target vector DBs: Qdrant (preferred for self-hosted enterprise profile) or Weaviate (preferred for SaaS/cloud-native). The choice is made at migration time based on then-current operational requirements.
- A `VectorSearchBackend` interface is already in place (or is added as a prerequisite to this story) so the migration is a configuration swap, not a code rewrite.
- Data migration uses a dual-write period (write to both pgvector and the new DB simultaneously for N queries) before cutting over reads.

---

## Edge Cases

- **Migration causes a latency regression (new DB slower than pgvector):** Roll back to pgvector using the dual-write period's fallback; investigate and re-plan.
- **Migration partial failure (some chunks not migrated):** Validate row counts before cutover; abort if count mismatch > 0.1%.
- **Trigger signals are borderline (e.g., 1 signal clearly met, 1 borderline):** Document the measurement and escalate to the AI Solutions Architect for a judgment call; do not auto-migrate on ambiguous signals.

---

## Technical Notes / Implementation Considerations

- **`VectorSearchBackend` interface:**
  ```python
  class VectorSearchBackend(Protocol):
      async def search(self, query_embedding: list[float], top_k: int, source_ids: list[str]) -> list[ChunkResult]: ...
      async def upsert(self, chunk: Chunk) -> None: ...
  ```
- **pgvector implementation:** Existing code refactored to implement this interface.
- **Qdrant implementation:** A new `QdrantVectorSearchBackend` class; configured via `VECTOR_SEARCH_BACKEND=qdrant` env var.
- **Migration script:** `scripts/migrate_vector_db.py` — reads all `Chunk` records from Postgres, upserts embeddings into the target vector DB, validates counts, then toggles the `VECTOR_SEARCH_BACKEND` env var.
- **Dual-write period:** Set `VECTOR_SEARCH_DUAL_WRITE=true` for N queries; reads from pgvector; writes to both. After N queries, compare result sets for a sample; if consistent, cut over reads to the new backend.

---

## Definition of Done

**If no migration (< 2 signals):**
- [ ] Trigger criteria evaluated against current measurements.
- [ ] "No migration" decision record filed with measurement values and next evaluation date.

**If migration (≥ 2 signals):**
- [ ] `VectorSearchBackend` interface implemented; `PgvectorBackend` and `QdrantBackend` both implementing it.
- [ ] Migration script (`scripts/migrate_vector_db.py`) implemented and tested against a copy of the production dataset.
- [ ] Dual-write period executed; read consistency validated.
- [ ] Full cutover executed; latency measurements confirm improvement.
- [ ] Zero data loss verified (chunk count match).
- [ ] Rollback plan tested (revert to pgvector).
- [ ] Architecture documentation updated.

---

## Priority

**Trigger-based** — not assigned to a fixed PI; evaluated at each PI boundary.

## Estimated Effort

**XL (Extra Large)** if migration proceeds — ~2 weeks (interface design, dual-write, migration script, validation, cutover).  
**S (Small)** if no migration — ~0.5 days (measurement evaluation and decision record).

## Related Epics / Features

- FEAT-20 (Vector database graduation)
- NFR-001 (Scalability)
- [Technology Architecture §6a](../../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path)
