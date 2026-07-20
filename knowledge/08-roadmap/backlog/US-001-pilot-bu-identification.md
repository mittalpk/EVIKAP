# US-001 — Pilot Business Unit Identification & Source-System Access Confirmation

## User Story

**As a** Program Lead / AI Solutions Architect,  
**I want to** identify and formally confirm a pilot business unit and secure read-level access to their top two knowledge sources (code repository + internal wiki),  
**So that** the Problem/Solution Fit validation activities in PI-0 can begin with real content and real stakeholders rather than synthetic assumptions.

---

## Description

Before any technical build work can proceed, the platform needs a committed pilot sponsor and access to real source systems. This story covers the stakeholder engagement, scoping, and access-provisioning activities that are the entry criterion for all other PI-0 work. Without this, all downstream validation stories (US-002, US-003) are blocked.

---

## Business Value

- Converts the EVIKAP program from a theoretical exercise to a real, scoped pilot with a committed sponsor.
- Establishes the concrete knowledge sources (repo + wiki) that will be used in all validation and MVP work.
- Aligns with the [Epic Hypothesis Gate 0](../EPIC_HYPOTHESIS.md) funding criterion: no PI-1 funding without validated discovery.

---

## Acceptance Criteria

**Given** the program has no committed pilot sponsor,  
**When** the Program Lead conducts stakeholder engagement per the [PI-0 objectives](../../06-agile-delivery/PI_PLANNING_OBJECTIVES.md),  
**Then:**
- A named pilot business unit is formally committed with a sponsor sign-off document.
- The sponsor confirms at least two source systems (one code repo, one internal wiki) to be indexed.
- Read-only, least-privilege credentials/tokens for those source systems are provisioned and verified (connection test passes).
- The pilot scope (question types, user population, time window) is documented and agreed.
- A data sensitivity classification for each source system is completed by the source system owner (per [Data Architecture §6](../../04-solution-architecture/DATA_ARCHITECTURE.md#6-data-classification-and-handling)).

---

## Functional Requirements

- FR-006 (Permission-aware retrieval) — access provisioning must be least-privilege from day one.
- FR-007 (Source registration) — source system details captured in a format compatible with the future source registry schema.

---

## Non-Functional Requirements

- NFR-002 (Security) — credentials must be stored in a secrets manager (not plaintext, not committed to source control) from the moment they are provisioned.
- NFR-004 (Compliance) — sensitivity classification must be signed off by the source system owner before any indexing begins.

---

## Dependencies

- Stakeholder engagement plan per [Business Analysis Plan §3](../../03-business-analysis/BUSINESS_ANALYSIS_PLAN.md).
- Source system owners must be identified and engaged.
- Secrets management infrastructure must be ready to receive new credentials (Azure Key Vault or equivalent).

---

## Assumptions

- At least one business unit has been informally identified as a candidate pilot sponsor before PI-0 begins.
- The source systems are accessible via a standard API (GitHub API for code, REST/XML for wiki).
- The sensitivity classification will be "internal-general" or "internal-sensitive" — regulated data (PII/PHI) is explicitly out of scope for the MVP pilot per [MVP Definition §3](../../05-lean-product/MVP_DEFINITION.md).

---

## Edge Cases

- **No willing pilot sponsor found:** Escalate to budget owner (CTO/Head of AI Platform); program gate 0 cannot be passed until a sponsor is confirmed.
- **Source system owner refuses indexing access:** Document the refusal, propose an alternative source, and escalate to the pilot sponsor if no alternative is available.
- **Source system uses non-standard auth (e.g., SAML-only):** Log as a blocker in [ISSUE_LOG.md](../ISSUE_LOG.md); do not attempt to work around it without security review.

---

## Technical Notes / Implementation Considerations

- This story produces no code changes — it produces documents: a pilot scope agreement, credential provisioning records, and sensitivity classification sign-offs.
- Credentials must follow the [Compliance & Security Framework §2](../../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md) secret-handling controls from the outset.
- Source system metadata (type, connection reference, sensitivity, refresh cadence, owner) should be recorded in a format that directly maps to the `Source` entity in [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial) — it will be migrated into the live source registry in PI-1.

---

## Definition of Done

- [ ] Named pilot business unit confirmed with written sponsor sign-off.
- [ ] At least two source systems scoped (one code repo, one wiki).
- [ ] Least-privilege read credentials provisioned and stored in secrets manager.
- [ ] Connection test passes for each source system (basic API call returns data).
- [ ] Sensitivity classification document signed by source system owner.
- [ ] Pilot scope document (question types, user population, time window) agreed and filed.
- [ ] All outputs filed as inputs to US-002 (time-motion survey) and US-004 (security design spike).

---

## Priority

**High** — Blocks all other PI-0 stories and all of PI-1.

## Estimated Effort

**M (Medium)** — ~3–5 days of stakeholder engagement, meetings, and documentation. No coding required.

## Related Epics / Features

- EPIC-01 (EVIKAP platform delivery)
- Discovery phase gate: [Problem/Solution Fit §4](../../05-lean-product/PROBLEM_SOLUTION_FIT.md#4-validation-sequencing-and-gates)
- Execution Runbook §3.1
