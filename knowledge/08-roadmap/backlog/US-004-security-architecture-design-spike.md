# US-004 — Security Architecture Design Spike — Permission Enforcement

## User Story

**As a** Security Engineer / AI Solutions Architect,  
**I want to** design and document the permission-enforcement architecture for the code and wiki source connectors, and have it reviewed by the Architecture Review Board (ARB),  
**So that** the permission-aware retrieval implementation in PI-1 (US-014, US-015) begins with a formally reviewed design and no unresolved high-severity findings — a hard prerequisite for indexing any real source content.

---

## Description

Permission-aware retrieval (FR-006) is a hard gate: no real content may be indexed until this design has passed ARB review. This story is a design spike (no production code) that produces a security architecture decision record covering: how requester identity flows from the interface tier to the retrieval tier, how per-source ACL checks are performed, how the permission cache works (TTL, invalidation, re-verification), and how over-exposure is detected and tested.

---

## Business Value

- Unblocks US-014 (permission-aware retrieval) and US-015 (permission matrix test suite), which are the hardest prerequisites to PI-1 go-live.
- Gives the CISO and data governance office early sight of the access-control design — satisfying their "keep satisfied" engagement requirement.
- Produces the security architecture document required by [Architecture Governance §3](../../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals) for the Phase 0 → 1 gate.

---

## Acceptance Criteria

**Given** a confirmed pilot source system (code repo + wiki per US-001),  
**When** the Security Engineer produces a permission enforcement design document and presents it to the ARB,  
**Then:**
- The design covers: identity propagation path, per-source ACL check mechanism, permission cache schema (TTL, re-verification trigger), and over-exposure detection/test approach.
- The design is consistent with the trust-boundary principle: the agent tier never queries the permission cache or source systems directly — only the Knowledge API does.
- The ARB review is completed with no unresolved high-severity findings.
- The design is filed as an Architecture Decision Record (ADR) in the `knowledge/` tree.
- The design is explicitly referenced as the authoritative spec for US-014 and US-015 implementation.

---

## Functional Requirements

- Directly enables FR-006 (permission-aware retrieval).
- Must address the PermissionCache entity defined in [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial): requester_identity, source_id, access_level, cached_at, ttl.

---

## Non-Functional Requirements

- NFR-002 (Security) — the design must confirm: no source-system credentials in the agent tier; constant-time auth comparisons on all service-to-service calls; no timing-attack surface on permission checks.
- NFR-004 (Compliance) — the design must define what gets logged from permission checks for audit purposes.

---

## Dependencies

- US-001 complete (source system details known — required to design the per-source ACL mechanism).
- ARB meeting scheduled within the PI-0 time window.

---

## Assumptions

- The two pilot source systems (GitHub + wiki) use standard API-level permission mechanisms (GitHub token scopes; wiki space-level access).
- The ARB meets at least once within the PI-0 window.
- The permission cache will be backed by the same Postgres instance as the main data layer (Supabase demo or Azure Postgres enterprise) — not a separate store.

---

## Edge Cases

- **ARB identifies a high-severity finding:** Rework the design and schedule a follow-up review before PI-1 begins. Do not start US-014 until the finding is resolved.
- **Source system has no programmatic permission API (e.g., wiki requires LDAP group lookup):** Escalate to the source system owner; document the integration gap and proposed workaround in the ADR.
- **Permission cache TTL vs. source freshness conflict:** The design must address this explicitly — what happens if a user's permissions change between cache entries? Define the worst-case exposure window and get ARB sign-off on it.

---

## Technical Notes / Implementation Considerations

- **Output artefact:** A Markdown ADR filed under `knowledge/04-solution-architecture/` (or a new `05-security-architecture/` subfolder if the ARB prefers a dedicated section).
- **Design sections to cover:**
  1. Identity propagation: how `requester_identity` is established at the Interface tier and passed to the Knowledge API without tampering.
  2. Per-source ACL lookup: how the Knowledge API checks whether `requester_identity` has access to a given `Chunk.permissions_ref` at query time.
  3. Permission cache: schema, TTL policy, invalidation triggers, and re-verification on expiry.
  4. Over-exposure detection: how the permission matrix test suite (US-015) will confirm zero over-exposure.
  5. Audit logging of permission checks (feeding FR-008 / US-018).
- **No code is written in this story** — the output is the design document and the ARB sign-off record.

---

## Definition of Done

- [ ] Permission enforcement design document (ADR) written and filed in `knowledge/`.
- [ ] Design covers all five sections listed above.
- [ ] Design is consistent with the trust-boundary principle (agent tier has no direct permission-check access).
- [ ] PermissionCache entity design is consistent with [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial).
- [ ] ARB review completed with zero unresolved high-severity findings.
- [ ] ARB sign-off recorded (reviewer names + date) in the ADR.
- [ ] Document explicitly referenced from US-014 and US-015 as the implementation spec.

---

## Priority

**High** — Gates the entire PI-1 permission and security work. Hard prerequisite per [Architecture Governance §3](../../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals).

## Estimated Effort

**M (Medium)** — ~3–5 days (design, documentation, ARB presentation prep, review cycle).

## Related Epics / Features

- FEAT-06 (Permission-aware retrieval)
- FEAT-11 (Platform hardening — security slice)
- Execution Runbook §3.4
- [Problem/Solution Fit §3 — security gate](../../05-lean-product/PROBLEM_SOLUTION_FIT.md#3-solution-validation-does-this-specific-solution-fit-the-validated-problem)
