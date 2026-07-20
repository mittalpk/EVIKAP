# US-020 — Feedback → Evaluation Dataset Routing

## User Story

**As an** AI Engineer,  
**I want to** automatically route negative feedback submissions into the evaluation dataset review queue so that flagged answers are reviewed and either corrected (added as a negative `EvaluationCase`) or dismissed,  
**So that** the evaluation harness (US-021) gets continuously enriched by real user quality signals rather than remaining static.

---

## Description

This story closes the loop between US-019 (feedback capture) and US-021/US-022 (evaluation harness). When a user submits a negative rating (👎), the corresponding query + answer is added to a `FeedbackReview` queue. An AI engineer reviews the queue, decides whether the case reveals a genuine retrieval failure, and if so, promotes it to an `EvaluationCase` record with the correct expected answer. A positive rating can also optionally promote a case as a confirmed-correct example.

---

## Business Value

- Converts user feedback from a passive signal into an active quality-improvement mechanism.
- Satisfies FR-009 acceptance check: "a flagged response appears in the evaluation-harness review queue within one indexing cycle."
- Grows the golden dataset organically without requiring the AI engineer to manually generate all cases.

---

## Acceptance Criteria

**Given** a negative feedback record exists in the `feedback` table (from US-019),  
**When** the feedback routing job runs (scheduled: once per day for PI-1),  
**Then:**
- A `FeedbackReviewItem` record is created in the database, linked to the `feedback.id` and `query.id`.
- The `FeedbackReviewItem` appears in the admin feedback review queue at `GET /api/v1/admin/feedback-review`.
- An AI engineer can mark a `FeedbackReviewItem` as: `promote_to_evaluation` (creates an `EvaluationCase`), `dismiss`, or `needs_more_investigation`.
- A promoted case creates an `EvaluationCase` record with the `golden_query` from the original query and an empty `golden_answer` field that the engineer must fill in before the case is activated.
- Activated `EvaluationCase` records are included in the next RAGAS evaluation run (US-021).
- The FR-009 acceptance check passes: a flagged response is in the review queue within one day.

---

## Functional Requirements

- FR-009 (Feedback and correction loop — routing step).

---

## Non-Functional Requirements

- NFR-011 (AI Quality Assurance) — promoted `EvaluationCase` records enrich the dataset version that RAGAS runs against; dataset version is incremented when new cases are activated.

---

## Dependencies

- US-019 (Feedback capture) — `feedback` table and records.
- US-021 (RAGAS evaluation harness) — promoted cases feed into the dataset it runs against.
- US-016 (RBAC) — feedback review endpoint is admin-only.

---

## Assumptions

- The routing job runs as a scheduled cron task (daily at midnight for PI-1); a proper async task queue (Celery/ARQ) is a PI-2 improvement.
- Only negative feedback is automatically routed; positive feedback is stored but not automatically promoted (optional manual promotion).
- An `EvaluationCase` is not active until the `golden_answer` is filled in by the reviewer — partial cases do not affect CI evaluation runs.

---

## Edge Cases

- **Feedback references a `query_id` not found:** Log and skip; do not create a `FeedbackReviewItem` for a dangling reference.
- **Same query flagged by multiple users:** Create one `FeedbackReviewItem` referencing all associated `feedback.id`s (or the most recent). Do not duplicate.
- **AI engineer promotes a case with an empty `golden_answer`:** Allow promotion to the queue but mark it `inactive`; the case must not affect evaluation runs until `golden_answer` is filled.

---

## Technical Notes / Implementation Considerations

- **New DB tables:** `feedback_review_items (id, feedback_id FK, query_id FK, status ENUM('pending','promoted','dismissed','needs_investigation'), reviewed_by, reviewed_at)`.
- **Routing job:** `scripts/route_feedback.py` — reads `feedback` where `rating='negative'` and `status='unprocessed'`; creates `FeedbackReviewItem` records; marks processed feedback as `status='routed'`.
- **Admin review API:**
  - `GET /api/v1/admin/feedback-review` — paginated list of pending `FeedbackReviewItem` records with query + answer detail.
  - `POST /api/v1/admin/feedback-review/{id}/action` — `{"action": "promote"|"dismiss"|"needs_investigation", "golden_answer": "..."}`.
- **Admin UI:** A `FeedbackReview` admin page in the frontend — a table of pending items with an action panel.
- **Dataset versioning:** When a new `EvaluationCase` is activated, increment `evaluation_dataset_version` in a config table; the next RAGAS run picks up the new version.

---

## Definition of Done

- [ ] `feedback_review_items` table created via Alembic migration.
- [ ] `route_feedback.py` script routes negative feedback to the review queue.
- [ ] Admin review API endpoints implemented (list + action).
- [ ] `FeedbackReview` admin UI page implemented.
- [ ] Promoted cases create `EvaluationCase` records with `inactive` status until `golden_answer` is filled.
- [ ] Activated cases increment `evaluation_dataset_version`.
- [ ] FR-009 acceptance check met: a flagged response appears in the review queue within one day.
- [ ] Unit tests: routing job, action endpoint, promotion to `EvaluationCase`.
- [ ] CI passes.
- [ ] Execution Runbook §4.6 (feedback routing bullet) marked `[x]`.

---

## Priority

**Medium** — Valuable for ongoing quality improvement but does not block pilot launch.

## Estimated Effort

**M (Medium)** — ~3–4 days (DB table, routing script, admin API + UI, tests).

## Related Epics / Features

- FEAT-09 (Feedback and correction loop — routing)
- FEAT-16 (RAG evaluation harness — dataset enrichment)
- Execution Runbook §4.6
