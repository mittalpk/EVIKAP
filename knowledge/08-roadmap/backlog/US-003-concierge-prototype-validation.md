# US-003 — Concierge Prototype Validation Run

## User Story

**As a** Business Analyst / AI Engineer,  
**I want to** manually run a concierge-style retrieval + LLM synthesis session over a small, real question set from pilot users,  
**So that** we validate that the solution concept (unified semantic retrieval + cited answers) actually satisfies the problem before committing PI-1 engineering resources to building the real platform.

---

## Description

A "concierge prototype" is a deliberate throwaway: a human manually retrieves information from the pilot source systems, feeds it to an LLM, and presents the result to pilot users as if it were the automated system. This validates whether the solution concept earns user trust and preference, not whether the engineering is complete. It is explicitly not production code — do not build a reusable system from this work.

Per [MVP Definition §6](../../05-lean-product/MVP_DEFINITION.md#6-mvp-as-an-architectural-down-payment-not-a-throwaway), the concierge prototype is the only "throwaway" phase; the PI-1 MVP onwards is built on the real target architecture.

---

## Business Value

- De-risks the largest unknown before any engineering investment: "Will users trust and prefer cited, AI-synthesised answers?"
- Produces the trust/usefulness ratings required for the PI-0 Gate exit.
- Surfaces question types the current keyword-search approach handles poorly — informing FEAT-02's retrieval scope.

---

## Acceptance Criteria

**Given** a set of ≥10 real questions from pilot users (collected in US-002),  
**When** the AI Engineer manually retrieves relevant content from the confirmed source systems and synthesises a cited answer using an LLM prompt,  
**Then:**
- Each answer is presented to the requesting user with citations (source, section, URL).
- Each user rates the answer on: trustworthiness (1–5) and usefulness vs. their current method (1–5).
- ≥60% of responses score ≥4/5 on trustworthiness.
- ≥50% of users prefer the concierge answer over their current search approach.
- Results are documented and reviewed by the pilot sponsor.
- The concierge prototype session notes are filed as an input to the Gate 0 decision (US-004 and the PI-0 exit review).

---

## Functional Requirements

- Manually exercises the concept behind FR-001 (unified query interface) and FR-003 (provenance and citation).
- No new code artefacts are produced or committed to the repository.

---

## Non-Functional Requirements

- NFR-003 (Privacy) — questions and answers must be anonymised before any filing; do not store real user questions alongside identifiable information.
- Results must be treated as pilot-only, not as representative of production quality.

---

## Dependencies

- US-001 complete (source system access confirmed).
- US-002 complete or in progress (real question set available from pilot users).

---

## Assumptions

- A small set (10–20) of representative questions can be run within 2–3 working days.
- The AI Engineer has direct read access to the pilot source systems to manually retrieve content.
- A basic LLM prompt (e.g., Gemini API call with retrieved context) is sufficient for the prototype — no orchestration infrastructure needed.
- Pilot users are available for a 15-minute feedback session per question set.

---

## Edge Cases

- **Users do not trust the LLM-generated answer even with citations:** Document the reason (e.g., stale source, wrong source, hallucinated claim not caught manually). This is a signal to strengthen the citation discipline and source freshness checking in PI-1.
- **< 50% user preference rate:** Review whether the question types selected are unrepresentative or the source content quality is too low. Discuss with the sponsor whether to pivot scope or proceed with that finding explicit in the Gate 0 report.
- **Source system access is too slow for manual retrieval to feel realistic:** Note in the prototype debrief; this informs latency requirements for the real system (NFR-006).

---

## Technical Notes / Implementation Considerations

- **Tooling:** Use a simple Python script or even a Jupyter notebook for the manual retrieval + prompt — this is not production code and must not be committed to `main` or any long-lived branch.
- **Prompt template:** Include retrieved excerpts, source URLs, and explicit citation markers; ask the LLM to respond only from the provided context and flag if context is insufficient.
- **Session format:** Screen-share the response with the user; collect rating verbally or via a 2-question form. Keep the session under 15 minutes per question.

---

## Definition of Done

- [ ] ≥10 real questions from pilot users run through the concierge process.
- [ ] Each answer presented to the requesting user with citations.
- [ ] Trust and usefulness ratings collected for each response.
- [ ] ≥60% trustworthiness score ≥4/5.
- [ ] ≥50% user preference over current method.
- [ ] Session notes filed (anonymised) with the Gate 0 review package.
- [ ] Pilot sponsor has reviewed the results.
- [ ] No production code committed as a result of this story.

---

## Priority

**High** — Required for PI-0 gate exit; blocks the Gate 1 funding decision.

## Estimated Effort

**M (Medium)** — ~3–5 days (question curation, manual retrieval runs, user sessions, report).

## Related Epics / Features

- EPIC-01 (VigilRAG platform delivery)
- Execution Runbook §3.3
- [Problem/Solution Fit §3](../../05-lean-product/PROBLEM_SOLUTION_FIT.md#3-solution-validation-does-this-specific-solution-fit-the-validated-problem)
