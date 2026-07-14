# Execution Runbook

**Status:** Living document · **Version:** 1.0 · 2026-07-14
**Related:** [MIGRATION_IMPLEMENTATION_ROADMAP.md](MIGRATION_IMPLEMENTATION_ROADMAP.md) · [ISSUE_LOG.md](ISSUE_LOG.md) · [../06-agile-delivery/PROGRAM_BACKLOG.md](../06-agile-delivery/PROGRAM_BACKLOG.md)

---

## 1. Purpose

The [Migration and Implementation Roadmap](MIGRATION_IMPLEMENTATION_ROADMAP.md) says *what* needs to be true by the end of each phase. This runbook says *what to actually do, in order*, to get there — a concrete, checkable task sequence, not a strategic milestone list. It covers **Phase 0 (Discovery & Validation)** and **Phase 1 (Foundation & MVP)** only; runbooks for Phase 2+ are written once Phase 1 exits, since task-level detail that far out would be speculative rather than actionable.

**How to use this document:** work top to bottom within a phase. Check a box only when its done-check passes, not when the work "should" be done. If you hit a blocker, log it in [ISSUE_LOG.md](ISSUE_LOG.md) before moving on — don't silently skip a step.

## 2. Status legend

`[x]` done and verified · `[~]` in progress · `[ ]` not started · `(blocked)` see linked issue in [ISSUE_LOG.md](ISSUE_LOG.md)

## 3. Phase 0 — Discovery & Validation

Per [Roadmap §5](MIGRATION_IMPLEMENTATION_ROADMAP.md#5-sequenced-roadmap) and [Problem/Solution Fit](../05-lean-product/PROBLEM_SOLUTION_FIT.md). No production code changes in this phase — a throwaway prototype only.

- [ ] **3.1 Identify the pilot business unit and confirm source-system access.** Entry criterion per [Problem/Solution Fit §4](../05-lean-product/PROBLEM_SOLUTION_FIT.md#4-validation-sequencing-and-gates); blocks everything else in Phase 0.
- [ ] **3.2 Run the time-motion survey / interviews.** Per [Problem/Solution Fit §2](../05-lean-product/PROBLEM_SOLUTION_FIT.md#2-problem-validation-is-the-problem-real-here-at-this-magnitude). Done-check: baseline time-to-answer and fragmentation-cost numbers published, replacing the directional industry benchmarks in [Problem Statement §2.3](../PRODUCT_PROBLEM_STATEMENT.md#23-quantifying-the-business-impact).
- [ ] **3.3 Build and run the concierge-style prototype.** Manual/throwaway retrieval + LLM synthesis over a small real question set, per [Problem/Solution Fit §3](../05-lean-product/PROBLEM_SOLUTION_FIT.md#3-solution-validation-does-this-specific-solution-fit-the-validated-problem). Done-check: trust/usefulness ratings collected from sampled users.
- [ ] **3.4 Security architecture design spike + review.** Permission-enforcement design for code + wiki source types, reviewed by the Architecture Review Board per [Architecture Governance §3](../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals). Done-check: no unresolved high-severity finding.
- [ ] **3.5 Gate 0 decision.** Compare results against [Problem/Solution Fit §5 exit criteria](../05-lean-product/PROBLEM_SOLUTION_FIT.md#5-what-fit-looks-like-exit-criteria-for-this-phase). Only proceed to Phase 1 if all three validations clear — see [Epic Hypothesis funding gates](../06-agile-delivery/EPIC_HYPOTHESIS.md#staged-funding-gates-lean-startup-discipline-applied-to-safe-funding).

## 4. Phase 1 — Foundation & MVP

Per [Roadmap §5](MIGRATION_IMPLEMENTATION_ROADMAP.md#5-sequenced-roadmap) and [MVP Definition](../05-lean-product/MVP_DEFINITION.md). Status below reflects the actual state of the `OmegaNexus` repository as of this document's last update — some hardening tasks were completed ahead of the rest of Phase 1 because they were zero-risk, high-severity fixes that didn't need to wait for feature work.

### 4.1 Security & repo hygiene (done ahead of schedule)

- [x] **Purge leaked credentials from git history.** A committed Terraform state backup contained real Gemini API key and GitHub PAT values; purged via `git-filter-repo`, `.gitignore` pattern broadened, history force-pushed. See [ISSUE-001](ISSUE_LOG.md#issue-001), [Compliance & Security Framework §4](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md#4-incident-response-posture).
- [ ] **(blocked on you) Rotate the exposed Gemini API key and GitHub PAT.** A history rewrite does not undo exposure that already happened — treat both as compromised regardless. This cannot be done by an agent; requires action in the Google AI Studio / GitHub settings consoles.
- [x] **Remove hardcoded real infrastructure identifiers from source-controlled files.** Real Azure subscription ID, tenant ID, a live Container App hostname, and a private local project path were hardcoded across `.github/workflows/`, `terraform/`, `deployment/AZURE_DEPLOYMENT.md`, and both services' `config.py` defaults. All parameterized via env vars/secrets or replaced with placeholders. See [ISSUE-004 through ISSUE-008](ISSUE_LOG.md).
- [x] **Stand up a real CI test gate.** `.github/workflows/deploy.yml` (build-and-deploy-to-Azure-on-every-push, no test step) replaced with `.github/workflows/ci.yml` (path-filtered backend/agent pytest + frontend `tsc`+build validation, triggered on push and PR). This is the FEAT-11 "CI test gate blocks bad deploys" item from [PI-1 objectives](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md#3-pi-1--mvp-trust--adoption-validation) — note it is a **build/test** gate only; the **evaluation-harness** gate (retrieval/prompt/model quality regression checks) is still open, see 4.4 below.

### 4.2 Data layer (MVP scope: code + wiki sources only)

- [ ] Provision managed Postgres + pgvector per [Technology Architecture §3](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#3-target-technology-stack-by-layer) (enterprise profile) or Supabase per the [demo profile](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6-deployment-profiles), depending on which environment this build targets.
- [ ] Add `sqlalchemy`/`asyncpg` (or the chosen driver) to `backend/requirements.txt` — currently absent, which is why `deployment/deployment_plan.md`'s assumption of a working DB connection doesn't hold yet. See [ISSUE-010](ISSUE_LOG.md#issue-010).
- [ ] Implement the `Source`, `Document`/`Chunk` entities from [Data Architecture §5](../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial).
- [ ] Replace `GitHubSearchSubsystem`/wiki keyword search with embedding + hybrid retrieval (FR-002).
- [ ] Done-check: retrieval quality measured against a small hand-built golden set before wider rollout (per [Problem/Solution Fit §3](../05-lean-product/PROBLEM_SOLUTION_FIT.md#3-solution-validation-does-this-specific-solution-fit-the-validated-problem)).

### 4.3 Permission enforcement and citations

- [ ] Implement permission-matrix test suite per source connector (FR-006); do not index real content until this passes security review.
- [ ] Implement citation rendering tying each answer claim to a retrieved chunk (FR-003).
- [ ] Replace the single hardcoded admin auth path with the RBAC foundation (NFR-002 slice for PI-1).

### 4.4 RAG evaluation harness (FEAT-16, NFR-011)

- [ ] Install and configure **RAGAS** against the retrieval/synthesis pipeline; if a metric RAGAS doesn't cover is needed, add **DeepEval** as a supplement rather than replacing RAGAS wholesale.
- [ ] Build the initial golden dataset (`EvaluationCase` entities per [Data Architecture §5](../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial)) — start small (20–50 representative query/answer pairs across code + wiki), grow it via the feedback loop (4.5 below) rather than trying to make it comprehensive on day one.
- [ ] Wire evaluation runs to persist `EvaluationRun` records (pipeline version, dataset version, faithfulness/context-precision/context-recall scores) — this record is what Model/System Cards (Phase 2, FEAT-19) will later cite, so get the schema right now rather than retrofitting it.
- [ ] Add the evaluation run as a required CI check (closes the "build/test gate only" caveat noted in 4.1 — `ci.yml` currently validates builds and unit tests, not AI quality).
- [ ] Done-check: a deliberately-introduced retrieval regression (e.g., reverting to keyword-only matching on a test branch) is caught by the CI gate before merge.

### 4.5 Guardrails (FEAT-17, FR-012)

- [ ] Install **Guardrails AI** or **NVIDIA NeMo Guardrails**; configure an evidence-in check that scans retrieved chunks for known prompt-injection patterns before they reach the synthesis model.
- [ ] Configure an answer-out check that validates synthesized output against a structural/safety schema before it's returned to the caller.
- [ ] Install **Microsoft Presidio** for PII detection/redaction (NFR-003) — a distinct concern from injection defense; don't conflate the two in one control.
- [ ] Build a maintained fixture test suite of known prompt-injection patterns embedded in sample source documents; run it in CI alongside the RAG evaluation harness (4.4).
- [ ] Done-check: every fixture in the injection test suite is blocked or neutralized; a fixture producing a malformed/unsafe output is rejected before delivery, not just logged.

### 4.6 Audit and feedback (minimal MVP versions)

- [ ] Implement the minimal audit log (FR-008: query, requester identity, evidence used, answer) — includes `guardrail_flags` from 4.5 so guardrail interventions are auditable, not silent.
- [ ] Implement feedback capture (FR-009: thumbs up/down feeding the evaluation dataset built in 4.4).

### 4.7 Unified query interface

- [ ] Ship the interactive UI query flow (FR-001) against the upgraded retrieval/orchestration stack.
- [ ] Done-check: MVP success criteria from [MVP Definition §5](../05-lean-product/MVP_DEFINITION.md#5-mvp-success-criteria-gono-go-for-full-program-backlog-investment) measured and reviewed at the Gate 1→2 decision point.

## 5. What's explicitly not in this runbook

Phase 2 (genuine iterative agent reasoning, database source connector, retrieval reranking, Model/System Card publication, vector database graduation evaluation, Terraform/network drift reconciliation, full observability) and Phase 3 (MCP interface, enterprise-scale load testing) are sequenced in the [Roadmap](MIGRATION_IMPLEMENTATION_ROADMAP.md#5-sequenced-roadmap) but not broken into runbook tasks yet — add that detail as a new numbered section here (before "Runbook maintenance", renumbering it accordingly) once Phase 1 exits, rather than speculating on task-level detail this far ahead. Phase 4+ (knowledge graph/GraphRAG, FEAT-13) is further out still and gets its own runbook section only once Phase 3 exits.

## 6. Runbook maintenance

Update checkboxes as work actually completes — this document should always reflect real repository state, not planned state (that's what the Roadmap and Program Backlog are for). Any blocker encountered while executing a task goes in [ISSUE_LOG.md](ISSUE_LOG.md) first, with a link back to the task here.
