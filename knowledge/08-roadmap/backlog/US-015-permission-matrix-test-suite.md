# US-015 — Permission Matrix Test Suite — Code & Wiki Sources

## User Story

**As a** Security Engineer / QA Engineer,  
**I want to** implement an automated permission matrix test suite that verifies zero over-exposure across a representative set of restricted/unrestricted chunk pairs for the GitHub and wiki source types,  
**So that** the security review of the permission-aware retrieval implementation (US-014) has machine-verifiable evidence and CI catches regressions before they reach production.

---

## Description

The acceptance check for FR-006 is: "a permission-matrix test suite confirms zero over-exposure." This story implements that suite. It covers both source types (GitHub repo with private/public files, Confluence with restricted/public pages), using fixture data (not real pilot content), and runs as part of the CI pipeline.

---

## Business Value

- Converts the "zero permission violations" security guarantee from a claim to a continuously-verified CI gate.
- Required for security sign-off before any real pilot content is indexed.
- Protects the platform from regression: any future change to the permission filter that introduces over-exposure is caught automatically before merge.

---

## Acceptance Criteria

**Given** the permission-aware retrieval (US-014) is implemented and fixture chunks with various `permissions_ref` configurations are loaded into a test database,  
**When** the permission matrix test suite runs,  
**Then:**
- A restricted chunk (e.g., `allowed_identities: ["admin@org.com"]`) is never returned for a query issued by `user@org.com`.
- A public chunk (`visibility: public`) is returned for any valid `requester_identity`.
- A chunk with `permissions_ref: null` is never returned (fail-closed behaviour).
- A chunk restricted to a group `["team-a"]` is not returned for an identity not in `team-a` (PI-1 simplification: group names must be in `allowed_identities` list directly for PI-1 — see US-014 assumptions).
- All test cases pass in CI on every push to `main` and on every PR.
- The test suite covers ≥10 distinct permission scenarios per source type (GitHub + Wiki = ≥20 total scenarios).

---

## Functional Requirements

- FR-006 (Permission-aware retrieval — automated acceptance verification).

---

## Non-Functional Requirements

- NFR-002 (Security) — the test suite uses fixture data only; never connects to real source systems in CI.
- NFR-010 (Maintainability) — new permission scenarios can be added as a new row in a fixture YAML without modifying test code.

---

## Dependencies

- US-014 complete (permission-aware retrieval implemented).
- Test database fixture setup (in-memory SQLite for CI, or a seeded test Postgres container).

---

## Assumptions

- Test fixtures are defined in a YAML file: `backend/tests/fixtures/permission_matrix.yaml`. Each entry: `identity`, `chunk_permissions_ref`, `expected_result` (`included` / `excluded`).
- CI uses the in-memory SQLite backend (`aiosqlite`) for the permission matrix tests — no live Postgres required.
- Group-based permission scenarios in PI-1 are simulated by including group names directly in `allowed_identities` (no group resolution API call in CI fixture tests).

---

## Edge Cases

- **New source type added in a future sprint:** The fixture YAML must be extended with ≥5 scenarios for the new source type before the connector goes to production.
- **Permission schema change (e.g., adding `allowed_groups` resolution in PI-2):** Update the test suite and fixtures as part of the US-016 or PI-2 permission story; the test suite must not rely on internal implementation details, only on the public retrieval endpoint behaviour.

---

## Technical Notes / Implementation Considerations

- **Test structure:** `backend/tests/test_permission_matrix.py` — parameterised pytest tests driven by `permission_matrix.yaml`.
- **Fixture YAML schema:**
  ```yaml
  - id: "scenario-001"
    description: "Private chunk not returned for non-owner"
    chunk_permissions_ref: '{"visibility": "private", "allowed_identities": ["admin@org.com"]}'
    requester_identity: "user@org.com"
    expected_result: "excluded"
  ```
- **Test isolation:** Each test case seeds a single `Chunk` record with the specified `permissions_ref`, calls the retrieval endpoint with the specified identity, and asserts the chunk is or is not in the result.
- **CI integration:** Add to the `backend-test` job in `.github/workflows/ci.yml` — runs alongside existing backend pytest suite.

---

## Definition of Done

- [ ] `permission_matrix.yaml` fixture file created with ≥20 scenarios (≥10 per source type).
- [ ] `test_permission_matrix.py` implemented with parameterised pytest tests driven by the YAML.
- [ ] All scenarios pass against the US-014 permission filter implementation.
- [ ] Test suite added to `ci.yml` `backend-test` job.
- [ ] Security sign-off: security engineer confirms the scenario coverage is sufficient for the pilot go-live gate.
- [ ] CI passes.

---

## Priority

**High** — Required for security sign-off and pilot go-live.

## Estimated Effort

**M (Medium)** — ~2–3 days (fixture YAML, parameterised tests, CI integration, security review cycle).

## Related Epics / Features

- FEAT-06 (Permission-aware retrieval — acceptance verification)
- FEAT-11 (Platform hardening — CI security gate)
- Execution Runbook §4.3
