# US-021 — RAGAS Evaluation Setup & Golden Dataset Bootstrap

## User Story

**As an** AI Engineer,  
**I want to** set up the RAGAS evaluation framework against the retrieval and synthesis pipeline and run it against the golden dataset (seeded in US-009),  
**So that** every retrieval/prompt/model change has an automated quality measurement and the evaluation harness can gate CI in US-023.

---

## Description

RAGAS measures three key RAG quality metrics: **faithfulness** (is the answer faithful to retrieved evidence?), **context precision** (is the retrieved context relevant?), and **context recall** (does the retrieved context cover the answer?). This story installs RAGAS, writes the evaluation runner, runs a first evaluation against the golden dataset, and establishes the baseline scores that future CI runs will compare against.

---

## Business Value

- Closes the single biggest quality risk in the current platform: "no automated evaluation, retrieval changes have no regression signal."
- Satisfies NFR-011 (AI Quality Assurance) — the automated gate that FR-003's ≥90% groundedness acceptance check is measured against.
- Elevated to "Must/PI-1" per [MVP Definition §3](../../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp): ungated retrieval changes against real content are unacceptable.

---

## Acceptance Criteria

**Given** the golden dataset is loaded as `EvaluationCase` records (US-009) and the hybrid retrieval endpoint is live (US-008),  
**When** the RAGAS evaluation runner is executed,  
**Then:**
- RAGAS is installed as a dependency in `backend/requirements.txt`.
- The evaluation runner (`scripts/run_evaluation.py`) iterates over all active `EvaluationCase` records.
- For each case, it calls the retrieval endpoint to get evidence and the synthesis endpoint to get an answer.
- RAGAS metrics are computed: `faithfulness`, `context_precision`, `context_recall` (and `answer_relevancy` if applicable).
- An `EvaluationRun` record is persisted with: `pipeline_version`, `dataset_version`, all metric scores, `run_at`.
- A summary report is printed/logged (mean scores per metric, per-case breakdown).
- The initial baseline `EvaluationRun` record is created and stored.

---

## Functional Requirements

- FR-003 acceptance check: RAGAS `faithfulness` score ≥90% target (not yet the CI gate — that is US-023; this story establishes the baseline).

---

## Non-Functional Requirements

- NFR-011 (AI Quality Assurance) — this is the primary implementation of the quality harness.
- NFR-010 (Maintainability) — RAGAS evaluation is independently runnable as a script; not coupled to application startup.

---

## Dependencies

- US-008 (hybrid retrieval endpoint) — called by the evaluation runner.
- US-011 (API query endpoint for synthesis) — used for `faithfulness` evaluation.
- US-009 (golden dataset in `EvaluationCase` table).
- `EvaluationRun` DB table — add via Alembic migration in this story.

---

## Assumptions

- RAGAS is used as the primary framework (per [Execution Runbook §4.4](../EXECUTION_RUNBOOK.md#44-rag-evaluation-harness-feat-16-nfr-011)).
- If RAGAS cannot cover a specific metric, DeepEval is used as a supplement (not a replacement).
- The LLM used for RAGAS evaluation (the LLM-as-judge) is the same as the synthesis model (Gemini 2.5 Flash/Pro) — configurable.
- The evaluation runner is a CLI script, not a persistent service.
- `pipeline_version` is derived from the git commit hash at run time.

---

## Edge Cases

- **Evaluation case has no `golden_answer`:** Skip and log a warning; inactive cases are excluded from evaluation runs.
- **Retrieval endpoint returns no evidence for an evaluation case:** Record the case as failed (`faithfulness=0`, `context_recall=0`); do not skip.
- **RAGAS LLM API call fails:** Fail the evaluation run with a clear error; do not produce partial results silently.
- **Dataset version mismatch:** If the `EvaluationCase` table has been updated (new cases promoted from US-020), increment `dataset_version` and run a fresh baseline evaluation.

---

## Technical Notes / Implementation Considerations

- **RAGAS installation:** `ragas` added to `backend/requirements.txt`.
- **`EvaluationRun` table:** `(id, pipeline_version, dataset_version, faithfulness, context_precision, context_recall, answer_relevancy, run_at, passed_threshold: bool)`.
- **Runner script:** `scripts/run_evaluation.py` — loads `EvaluationCase` records, calls retrieval + synthesis, feeds to `ragas.evaluate()`, persists `EvaluationRun`.
- **RAGAS dataset format:** `ragas.Dataset` with columns: `question`, `answer`, `contexts` (list of retrieved chunk contents), `ground_truth` (from `EvaluationCase.golden_answer`).
- **Threshold for CI gate (US-023):** Set the initial threshold at the baseline run's score minus 5pp tolerance (e.g., if baseline `faithfulness`=0.82, CI threshold = 0.77). Document the threshold in `scripts/evaluation_config.yaml`.

---

## Definition of Done

- [ ] `ragas` added to `backend/requirements.txt`.
- [ ] `EvaluationRun` table created via Alembic migration.
- [ ] `scripts/run_evaluation.py` implemented and documented.
- [ ] First baseline evaluation run executed against the golden dataset.
- [ ] `EvaluationRun` baseline record persisted with all metric scores.
- [ ] Baseline scores documented in `scripts/evaluation_config.yaml` (with threshold).
- [ ] Summary report output confirmed.
- [ ] CI passes (script importable; unit tests mock the retrieval and synthesis calls).
- [ ] Execution Runbook §4.4 first three bullets marked `[x]`.

---

## Priority

**High** — Core quality gate infrastructure; required before pilot go-live.

## Estimated Effort

**M (Medium)** — ~3–4 days (RAGAS setup, runner script, DB migration, baseline run, config).

## Related Epics / Features

- FEAT-16 (RAG evaluation harness)
- NFR-011 (AI Quality Assurance)
- Execution Runbook §4.4
