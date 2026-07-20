# US-022 — EvaluationRun Record Persistence & Quality Trend Dashboard

## User Story

**As an** AI Engineer / Platform Owner,  
**I want to** view a dashboard showing the quality trend of RAGAS evaluation scores across all historical `EvaluationRun` records — per metric, per pipeline version, per dataset version — so that I can detect quality regressions and report on AI quality improvement at each PI boundary.

---

## Description

`EvaluationRun` records are persisted by US-021's runner script. This story provides the read interface: an API endpoint to query historical evaluation runs and a dashboard page in the admin UI to visualise the trend. This is the data that Model/System Cards (US-034) will cite, so the schema must be correct from day one.

---

## Business Value

- Provides the "production quality trend dashboard" required by NFR-011.
- Enables PI-boundary reviews to compare quality objectively (not by anecdote).
- The historical record is the source of truth for Model/System Card scores — getting the schema right now avoids a painful retrofit in PI-2.

---

## Acceptance Criteria

**Given** multiple `EvaluationRun` records exist from past evaluations (US-021),  
**When** an admin visits the Evaluation Dashboard in the admin UI,  
**Then:**
- A line chart shows `faithfulness`, `context_precision`, and `context_recall` trends over time (one data point per `EvaluationRun`).
- The chart can be filtered by `dataset_version` and `pipeline_version`.
- The latest run's scores are displayed prominently with a pass/fail indicator against the CI threshold.
- `GET /api/v1/admin/evaluation-runs` returns a paginated list of `EvaluationRun` records.
- `GET /api/v1/admin/evaluation-runs/latest` returns the most recent run.
- All endpoints are admin-only.

---

## Functional Requirements

- Supports FR-013 (Model/System Card publication — the scores a card must cite come from these records).

---

## Non-Functional Requirements

- NFR-011 (AI Quality Assurance — production quality trend dashboard required).
- NFR-012 (Governance and transparency — quality scores available for governance review).

---

## Dependencies

- US-021 (RAGAS evaluation runner — creates `EvaluationRun` records).
- US-016 (RBAC — admin-only endpoints).

---

## Assumptions

- The dashboard is a simple admin-only page, not a public-facing report.
- Chart rendering uses a lightweight library already in the frontend stack (e.g., `recharts` or `chart.js`).
- The dashboard shows all-time history; no archiving required for PI-1.

---

## Edge Cases

- **No evaluation runs recorded yet:** Show an empty state: "No evaluation runs recorded. Run `scripts/run_evaluation.py` to generate the first record."
- **Only one evaluation run:** Show a single data point chart (trend line requires ≥2 points; show a single point marker instead).

---

## Technical Notes / Implementation Considerations

- **API endpoints:**
  - `GET /api/v1/admin/evaluation-runs?dataset_version=&pipeline_version=` — paginated.
  - `GET /api/v1/admin/evaluation-runs/latest` — returns the single most recent `EvaluationRun`.
- **Frontend page:** `EvaluationDashboard.tsx` — a chart (recharts `LineChart`) and a summary table of recent runs.
- **Pass/fail indicator:** Compare `latest_run.faithfulness` against the threshold in `evaluation_config.yaml`; show a green ✓ or red ✗ badge.

---

## Definition of Done

- [ ] `GET /api/v1/admin/evaluation-runs` and `/latest` endpoints implemented and admin-only.
- [ ] `EvaluationDashboard` frontend page implemented with line chart and summary table.
- [ ] Pass/fail threshold badge confirmed.
- [ ] Empty state and single-run state handled gracefully.
- [ ] Unit tests: API endpoints (pagination, filtering, empty result, latest).
- [ ] CI passes.

---

## Priority

**High** — Required for PI-1 NFR-011 compliance and for Model/System Card schema correctness.

## Estimated Effort

**S (Small)** — ~2 days (API endpoints, frontend dashboard, tests; builds on US-021's DB records).

## Related Epics / Features

- FEAT-16 (RAG evaluation harness)
- FEAT-19 (Model/System Card publication — depends on `EvaluationRun` records)
- NFR-011 (AI Quality Assurance)
