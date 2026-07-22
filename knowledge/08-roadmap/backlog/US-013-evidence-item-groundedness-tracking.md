# US-013 — EvidenceItem Entity & Groundedness Score Tracking

## User Story

**As an** AI Engineer / Compliance Officer,  
**I want to** persist `EvidenceItem` records for every query — linking each retrieved chunk to the query it was used in, with its relevance score and whether it was included in the synthesised answer — and compute a per-answer groundedness score,  
**So that** the audit log (US-018), the evaluation harness (US-021), and Model/System Cards (US-034) can all cite real, stored evidence-path records rather than reconstructed approximations.

---

## Description

`EvidenceItem` is the backbone of provenance in VigilRAG ([Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial)). This story implements the persistence of `EvidenceItem` records after each query and computes the groundedness score (`Answer.groundedness_score`) by measuring what fraction of the synthesised answer's claims are traceable to returned chunks. This data is what FR-003's acceptance check ("≥90% of answer claims map to a cited source") is measured against.

---

## Business Value

- Makes the "provenance" claim real and auditable — not just a display feature but a stored, queryable record.
- Provides the data backbone for compliance queries: "what evidence did the system use when user X asked question Y?"
- The `groundedness_score` stored here is what the RAGAS evaluation harness (US-021) compares against its automated faithfulness metric.

---

## Acceptance Criteria

**Given** a query is processed by the agent tier (US-011),  
**When** evidence is retrieved and the answer is synthesised,  
**Then:**
- One `EvidenceItem` record is persisted per chunk returned by the retrieval step, linked to the `Query.id`.
- `EvidenceItem.relevance_score` is set from the retrieval endpoint's score.
- `EvidenceItem.rerank_score` is null in PI-1 (set by US-033 in PI-2).
- `EvidenceItem.used_in_answer` is `True` for chunks whose content is referenced in the synthesis, `False` for chunks retrieved but not used.
- `Answer.groundedness_score` is computed as `used_chunks / total_returned_chunks` (simple heuristic for PI-1; replaced by RAGAS faithfulness in PI-2).
- `Answer.guardrail_flags` is persisted from the Guardrails service response (empty list if no flags).
- A `Query` record is persisted at the start of each request with: `requester_identity`, `text`, `timestamp`.

---

## Functional Requirements

- FR-003 (Provenance and citation — stored, not just displayed).
- FR-008 (Audit and access review — `EvidenceItem` is the evidence trail for compliance queries).

---

## Non-Functional Requirements

- NFR-004 (Compliance) — `EvidenceItem` and `Answer` records must be retained per the data-retention policy; must not be deleted without a formal retention-policy action.
- NFR-007 (Observability) — the `trace_id` must link `Query`, `EvidenceItem[]`, and `Answer` records so a trace from the observability service resolves to the full evidence path.

---

## Dependencies

- US-008 (hybrid retrieval endpoint — provides `relevance_score` per chunk).
- US-011 (API query endpoint — assembles citations and synthesis).
- `EvaluationCase` DB table from US-009 (same Alembic migration cycle — may be combined).

---

## Assumptions

- `Query`, `EvidenceItem`, and `Answer` tables are added via a new Alembic migration in this story.
- The `used_in_answer` flag for PI-1 is set heuristically: a chunk is marked `used_in_answer=True` if any phrase from its `content` appears verbatim or near-verbatim in the synthesised answer (simple substring check). Proper LLM-based groundedness replaces this in US-021.
- Writes are async (fire-and-forget after the response is returned to the caller); a failure to persist `EvidenceItem` must be logged but must not cause the query response to fail.

---

## Edge Cases

- **Retrieval returns 0 chunks:** Persist a `Query` record and an `Answer` with `groundedness_score=null` and `citations=[]`.
- **Database write fails:** Log the error with `trace_id`; do not surface to the end user. The query response should still be returned.
- **Very high chunk count (> 20 evidence items):** Persist all; the `used_in_answer` flag will correctly mark only the subset actually used.

---

## Technical Notes / Implementation Considerations

- **Alembic migration:** Add `queries`, `evidence_items`, and `answers` tables. `evidence_items.query_id FK queries.id`, `answers.query_id FK queries.id`.
- **Persistence timing:** Write `Query` at request entry, `EvidenceItem[]` after retrieval, `Answer` after synthesis — all in a single async DB transaction per request, committed after synthesis is complete. If the transaction fails, log with `trace_id` and skip persistence (response still returned).
- **`used_in_answer` heuristic:** `any(chunk.content[:100] in answer_text for chunk in evidence_items)` — crude but sufficient for PI-1 audit trail and groundedness signal.
- **`groundedness_score` formula (PI-1):** `len([e for e in evidence if e.used_in_answer]) / len(evidence)`. Will be replaced by RAGAS faithfulness score in US-021/US-022.

---

## Definition of Done

- [ ] Alembic migration adds `queries`, `evidence_items`, `answers` tables with correct FK relationships.
- [ ] `Query`, `EvidenceItem[]`, and `Answer` records persisted for each query request.
- [ ] `EvidenceItem.used_in_answer` heuristic implemented.
- [ ] `Answer.groundedness_score` computed and stored.
- [ ] `Answer.guardrail_flags` stored (empty list for PI-1 with stub guardrails).
- [ ] Persistence failures logged but do not propagate to the API response.
- [ ] `trace_id` links all three record types.
- [ ] Unit tests: assert correct record creation, `used_in_answer` flag logic, groundedness calculation.
- [ ] CI passes.

---

## Priority

**High** — Foundational for audit (US-018), evaluation (US-021), and compliance.

## Estimated Effort

**M (Medium)** — ~2–4 days (Alembic migration, persistence logic, `used_in_answer` heuristic, tests).

## Related Epics / Features

- FEAT-03 (Provenance and citation)
- FEAT-08 (Audit log — `EvidenceItem` is the audit record)
- FEAT-16 (RAG evaluation — `groundedness_score` is the PI-1 quality signal)
