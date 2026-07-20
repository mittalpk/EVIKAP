# US-002 — Time-Motion Survey & Knowledge Fragmentation Baseline

## User Story

**As a** Program Lead / Business Analyst,  
**I want to** run structured time-motion interviews and a survey with pilot users to measure how long they currently spend locating answers across fragmented knowledge systems,  
**So that** we replace the directional industry benchmarks in the Problem Statement with real, sponsor-specific baseline numbers that make the MVP success criteria measurable against an honest starting point.

---

## Description

The [Product Problem Statement §2.3](../../PRODUCT_PROBLEM_STATEMENT.md) currently uses directional industry benchmarks (e.g., "19% of working time spent searching"). This story replaces those with actual measured baselines from the pilot business unit. The outputs are the denominator against which MVP success criteria (US-002 outputs → US-009 done-check) will be evaluated.

---

## Business Value

- Converts the ROI case from estimated to evidence-based, which is the condition for Gate 1 (PI-1 funding approval).
- Surfaces the specific question types and source combinations that matter most to pilot users, focusing the MVP scope.
- Provides the baseline "median time-to-answer" figure that the [MVP success criteria §5](../../05-lean-product/MVP_DEFINITION.md#5-mvp-success-criteria-gono-go-for-full-program-backlog-investment) require a ≥25% improvement against.

---

## Acceptance Criteria

**Given** a confirmed pilot business unit (US-001 complete),  
**When** the Business Analyst conducts time-motion interviews with ≥5 pilot users and collects survey responses from ≥10 users,  
**Then:**
- A median time-to-answer baseline (in minutes) is published for at least three representative in-scope question types.
- A fragmentation-cost figure (number of systems consulted per question, on average) is published.
- The top 10 most frequently asked question types within the pilot scope are documented.
- The directional benchmarks in [Problem Statement §2.3](../../PRODUCT_PROBLEM_STATEMENT.md#23-quantifying-the-business-impact) are replaced with the actual measured numbers.
- Results are reviewed and accepted by the pilot sponsor.

---

## Functional Requirements

- No system functionality — this is a research/measurement story.
- Outputs directly inform acceptance thresholds for US-009 (retrieval quality) and the MVP success criteria.

---

## Non-Functional Requirements

- NFR-003 (Privacy) — interview notes and survey responses must be anonymised before publication; no PII in the baseline report.

---

## Dependencies

- US-001 complete (confirmed pilot business unit and sponsor).
- Access to pilot users for interviews (arranged by pilot sponsor).

---

## Assumptions

- At least 10 pilot users are available and willing to participate in the survey within the PI-0 time window.
- The pilot sponsor can facilitate access to interview participants.
- "Time-to-answer" is measurable by self-report (time diary / recall survey) given the absence of system-level instrumentation in the current process.

---

## Edge Cases

- **Fewer than 10 survey respondents:** Report results with a confidence caveat; do not fabricate a sample size. Discuss with sponsor whether to extend the survey window or proceed with the available sample.
- **Users report very low fragmentation (< 2 systems per question):** This may indicate the pilot scope is too narrow; surface to the Program Lead for a scope discussion before proceeding.
- **Median time-to-answer is already < 5 minutes:** Re-examine whether the selected question types are representative; the problem hypothesis may not hold for this BU's specific context — document and escalate to the budget owner.

---

## Technical Notes / Implementation Considerations

- Deliverable format: a short research report (Markdown or PDF) with the headline metrics, methodology, raw anonymised data appendix, and a clear mapping from each metric to the relevant MVP success criterion.
- Survey tool: any standard tool (Google Forms, MS Forms); data must not be stored in any system connected to real source content.
- Interview structure: semi-structured, ~30 minutes per participant; questions covering: which systems they search, how often, how long it takes, confidence in the answer quality, and what types of questions they ask most.

---

## Definition of Done

- [ ] ≥5 interviews completed and notes filed (anonymised).
- [ ] ≥10 survey responses collected.
- [ ] Median time-to-answer baseline published per ≥3 question types.
- [ ] Fragmentation-cost figure (systems-per-question average) documented.
- [ ] Top 10 question types documented.
- [ ] Problem Statement §2.3 updated with real baseline numbers (with source note).
- [ ] Results reviewed and signed off by pilot sponsor.

---

## Priority

**High** — Required for PI-0 gate exit and Gate 1 funding decision.

## Estimated Effort

**M (Medium)** — ~5–8 days including scheduling, conducting, and analysing interviews/survey.

## Related Epics / Features

- EPIC-01 (EVIKAP platform delivery)
- Execution Runbook §3.2
- [Problem/Solution Fit §2](../../05-lean-product/PROBLEM_SOLUTION_FIT.md#2-problem-validation-is-the-problem-real-here-at-this-magnitude)
