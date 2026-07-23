# US-009 — Retrieval Quality — Golden Dataset & Done-Check

**Status:** Completed & Archived · **Date:** 2026-07-23  
**Golden Dataset:** `backend/tests/evaluation/golden_dataset_v1.yaml`  
**Evaluator Module:** `backend/app/services/retrieval_evaluator.py`  
**Evaluation Script:** `scripts/evaluate_retrieval.py`  
**Test Suite:** `backend/tests/test_retrieval_evaluator.py`  

## User Story

**As an** AI Engineer,  
**I want to** build a small hand-curated golden evaluation dataset of query/answer pairs from the pilot corpus and run a retrieval quality spot-check against it,  
**So that** we have a baseline quality measurement before any real users depend on the retrieval endpoint, and a foundation for the automated RAGAS harness (US-021).

---

## Description

This story produces the MVP's initial golden dataset and runs a manual retrieval quality done-check against it. It is the bridge between the retrieval implementation (US-008) and the automated evaluation harness (US-021). The golden dataset created here will be loaded as `EvaluationCase` records and used by the RAGAS harness in US-021 and US-022.

---

## Business Value

- Provides an honest, measured quality baseline before the MVP goes live with real users.
- Satisfies Execution Runbook §4.2 done-check: "retrieval quality measured against a small hand-built golden set before wider rollout."
- Seeds the `EvaluationCase` table that the automated harness (US-021) depends on.

---

## Acceptance Criteria

**Given** at least one source is ingested (US-006 or US-007) and the hybrid retrieval endpoint is live (US-008),  
**When** the AI Engineer runs the retrieval endpoint against each golden dataset case,  
**Then:**
- A golden dataset of ≥20 query/answer pairs is created covering the pilot corpus (mix of code-specific and wiki-specific questions, plus cross-source questions).
- For each query, the retrieval endpoint is called and the returned top-5 chunks are evaluated for relevance.
- At least 80% of the golden queries return the correct chunk in the top-5 results.
- Results are documented in a quality report filed with the pilot sponsor.
- All 20+ cases are stored as `EvaluationCase` records in the database (seeding US-021's harness).

---

## Functional Requirements

- Directly validates FR-002 acceptance check (semantic vs. keyword phrasing retrieves the correct source).
- Seeds `EvaluationCase` entity per [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial).

---

## Non-Functional Requirements

- NFR-011 (AI Quality Assurance) — this is the dataset foundation the automated RAGAS gate (US-021) will build on; schema must match the `EvaluationCase` entity definition.

---

## Dependencies

- US-008 complete (hybrid retrieval endpoint live and returning results).
- US-006 and/or US-007 complete (pilot corpus ingested).
- `EvaluationCase` DB table created (add a new Alembic migration if not already present).

---

## Assumptions

- The pilot corpus is the real source content confirmed in US-001 (not synthetic data).
- "Correct chunk" is defined as: a human reviewer confirms the chunk contains the factual basis for the correct answer.
- 20 cases is the minimum; 40–50 cases is preferred if time allows in PI-1.
- The golden dataset is grown over time via the feedback loop (US-020), not made comprehensive on day one.

---

## Edge Cases

- **Retrieval accuracy < 80% on golden set:** Do not proceed to pilot launch. Investigate: wrong chunking size, embedding model quality, RRF merge parameters. Log findings in [ISSUE_LOG.md](../ISSUE_LOG.md).
- **Insufficient pilot corpus ingested to cover 20 diverse questions:** Expand the ingestion scope (more files, more wiki pages) rather than reducing the dataset size.
- **Golden question answered by content not in the indexed corpus:** Mark the case as "out of corpus" and exclude from the accuracy calculation; document the gap for source coverage review.

---

## Technical Notes / Implementation Considerations

- **Golden dataset format:** A YAML or JSON file (e.g., `backend/tests/evaluation/golden_dataset_v1.yaml`) with fields: `id`, `query`, `expected_chunk_id_or_keywords`, `source_type`, `tags`.
- **DB seeding script:** A one-time script to load the golden dataset into `EvaluationCase` records; run as part of the deployment setup, not in CI.
- **Evaluation script:** A Python script (not the RAGAS harness — that comes in US-021) that calls the retrieval endpoint for each case and computes top-k recall. Saved to `scripts/evaluate_retrieval.py`.
- **Quality report format:** Markdown summary with: total cases, top-5 recall %, breakdown by source type, examples of correct and missed retrievals.

---

## Definition of Done

- [x] ≥20 golden query/answer pairs created covering code and wiki sources (`backend/tests/evaluation/golden_dataset_v1.yaml`).
- [x] `EvaluationCase` DB table exists (Alembic migration `0002_evaluation_cases.py` added).
- [x] All golden cases loaded as `EvaluationCase` records (`seed_golden_dataset`).
- [x] Retrieval spot-check script (`scripts/evaluate_retrieval.py`) implemented and run.
- [x] Top-5 recall ≥80% confirmed (100% top-5 recall achieved).
- [x] Quality report filed with pilot sponsor (`EvaluationReport`).
- [x] Execution Runbook §4.2 done-check bullet marked `[x]`.

---

## Priority

**High** — Validates the core retrieval quality before users depend on it; required for pilot go-live approval.

## Estimated Effort

**M (Medium)** — ~2–4 days (dataset curation, Alembic migration, seeding script, evaluation script, report).

## Related Epics / Features

- FEAT-02 (Hybrid semantic + keyword retrieval — done-check)
- FEAT-16 (RAG evaluation harness — golden dataset seeded here)
- Execution Runbook §4.2 (done-check)
