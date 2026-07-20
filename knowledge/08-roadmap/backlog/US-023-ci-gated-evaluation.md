# US-023 — CI-Gated Evaluation — Block Merge on RAGAS Regression

## User Story

**As an** AI Engineer / Tech Lead,  
**I want to** add the RAGAS evaluation run as a required CI check so that any pull request that causes a quality regression below the defined threshold is blocked from merging to `main`,  
**So that** retrieval logic, prompt, or model changes cannot reach production without passing an automated quality gate.

---

## Description

This story wires the RAGAS evaluation runner (US-021) into the CI pipeline (`ci.yml`). It adds a new CI job (`evaluation-gate`) that runs `scripts/run_evaluation.py` against a seeded test database (using the golden dataset), compares the output against the threshold in `evaluation_config.yaml`, and fails the job if any metric is below threshold. This closes the "build/test gate only" caveat noted in Execution Runbook §4.1 and Runbook §4.4.

---

## Business Value

- Converts the quality harness from a manual script into an enforced CI gate — the difference between "we measured quality once" and "quality is continuously protected."
- Satisfies NFR-010 (Maintainability): "CI pipeline demonstrably blocks a deploy on evaluation-harness regression."
- Satisfies NFR-011 (AI Quality Assurance): "CI blocks merge on a defined regression threshold against the prior baseline."

---

## Acceptance Criteria

**Given** a pull request is opened against `main` that modifies retrieval logic, prompts, or model configuration,  
**When** the CI pipeline runs the `evaluation-gate` job,  
**Then:**
- The evaluation runner executes against the CI golden dataset (using a seeded SQLite or Postgres test DB).
- If all RAGAS metrics are ≥ the thresholds in `evaluation_config.yaml`, the job passes (green ✓).
- If any metric falls below threshold, the job fails with a human-readable report: "faithfulness: 0.68 (below threshold 0.77 — BLOCKED)."
- The CI job requires no manual secrets (uses the same mock/SQLite setup as unit tests for the DB; uses the LLM API key secret for RAGAS's LLM-as-judge calls).
- Done-check: a deliberately-introduced retrieval regression (reverting to keyword-only on a test branch) is caught by the CI gate before merge.

---

## Functional Requirements

- This story is the enforcement mechanism for NFR-011's "CI blocks merge" requirement.

---

## Non-Functional Requirements

- NFR-010 (Maintainability) — the CI job must complete within a reasonable time budget (target: ≤10 minutes). If the full golden dataset evaluation takes longer, use a fast-CI subset (configurable in `evaluation_config.yaml`).
- NFR-011 (AI Quality Assurance) — threshold must be stored in version-controlled config (`evaluation_config.yaml`), not hardcoded in the CI YAML.

---

## Dependencies

- US-021 (RAGAS evaluation runner and `evaluation_config.yaml` with initial thresholds).
- US-022 (`EvaluationRun` record persistence — CI job persists its run record).
- GitHub Actions secret `GEMINI_API_KEY` (for RAGAS LLM-as-judge calls in CI).

---

## Assumptions

- The CI evaluation uses a small "fast-CI" subset of the golden dataset (e.g., 10 cases) to keep the job within the time budget. The full dataset is used in nightly/scheduled evaluation runs.
- `evaluation_config.yaml` specifies: `ci_dataset_size`, `thresholds.faithfulness`, `thresholds.context_precision`, `thresholds.context_recall`.
- The evaluation CI job is path-filtered: triggered on changes to `backend/app/`, `agent/app/`, or `scripts/run_evaluation.py`.

---

## Edge Cases

- **LLM API rate-limited during CI evaluation:** Retry with exponential backoff (built into the runner in US-021); if exhausted, fail the job with a clear error (not a silent pass).
- **Golden dataset not seeded in CI:** The CI job must seed the `EvaluationCase` records from `backend/tests/evaluation/golden_dataset_v1.yaml` at job start; fail with a clear error if the file is missing.
- **Threshold adjusted (e.g., raised after quality improvement):** The change to `evaluation_config.yaml` itself must trigger the CI gate — ensure path filtering includes that file.
- **False positive (flaky LLM judge):** If the CI job fails intermittently on the same commit, investigate RAGAS judge non-determinism; consider setting `temperature=0` for the LLM judge calls.

---

## Technical Notes / Implementation Considerations

- **New CI job in `.github/workflows/ci.yml`:**
  ```yaml
  evaluation-gate:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r backend/requirements.txt
      - name: Seed evaluation dataset
        run: python scripts/seed_evaluation_dataset.py --env ci
      - name: Run RAGAS evaluation
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python scripts/run_evaluation.py --mode ci --fail-on-regression
  ```
- **`--fail-on-regression` flag:** Makes the runner exit with code 1 if any threshold is breached; outputs the per-metric comparison report.
- **Path filtering:** Add `paths: ['backend/app/**', 'agent/app/**', 'scripts/run_evaluation.py', 'scripts/evaluation_config.yaml']` to the job trigger.
- **`seed_evaluation_dataset.py`:** A lightweight script that loads `golden_dataset_v1.yaml` into the CI SQLite DB (no live Postgres needed in CI).

---

## Definition of Done

- [ ] `evaluation-gate` CI job added to `ci.yml`.
- [ ] Job path-filtered to retrieval/agent/evaluation-script changes.
- [ ] Job seeds the fast-CI golden dataset subset at start.
- [ ] Job fails with a human-readable regression report when a threshold is breached.
- [ ] Done-check: deliberately reverting to keyword-only retrieval on a test branch causes the CI gate to fail.
- [ ] `EvaluationRun` record persisted for CI runs (with `pipeline_version=git-sha`).
- [ ] CI total runtime (all jobs) stays within a reasonable budget.
- [ ] Execution Runbook §4.4 fourth bullet marked `[x]`.

---

## Priority

**High** — The enforcement mechanism that makes all other quality work durable.

## Estimated Effort

**M (Medium)** — ~2–3 days (CI YAML, runner flags, seed script, regression done-check, path filtering).

## Related Epics / Features

- FEAT-11 (Platform hardening — CI gate)
- FEAT-16 (RAG evaluation harness — CI integration)
- NFR-010 (Maintainability)
- NFR-011 (AI Quality Assurance)
- Execution Runbook §4.4
