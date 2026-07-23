# US-014 — Permission-Aware Retrieval — Source ACL Enforcement

**Status:** Completed & Archived · 2026-07-23

## User Story


**As a** Security Engineer,  
**I want to** enforce per-source access controls at query time in the retrieval endpoint so that only chunks the requesting identity is permitted to access are ever returned, cited, or synthesised from,  
**So that** VigilRAG never returns content to a user who couldn't access it directly in the source system.

---

## Description

This is the implementation of FR-006 — the hardest security requirement and the one that must pass a formal security review before any real content is indexed. It builds on the design from US-004. The permission check runs at the Knowledge API layer (retrieval tier), not in the agent or interface tier, consistent with the trust-boundary principle. Chunks with `permissions_ref` indicating restricted access are filtered out of retrieval results before they are returned to the agent tier.

---

## Business Value

- Is a non-negotiable hard gate for pilot go-live: "zero permission-enforcement violations" is a binary success criterion per [MVP Definition §5](../../05-lean-product/MVP_DEFINITION.md#5-mvp-success-criteria-gono-go-for-full-program-backlog-investment).
- Gives the CISO the provable answer to: "what can the AI system see on behalf of a given user?"

---

## Acceptance Criteria

**Given** a query is issued with a `requester_identity` claim,  
**When** the hybrid retrieval endpoint (US-008) runs the permission filter,  
**Then:**
- Chunks with `permissions_ref` indicating access is restricted to identities other than `requester_identity` are excluded from the returned `EvidenceItem` list.
- The filter is applied after the vector + keyword merge (RRF) but before results are returned to the agent tier.
- The filter result is logged (how many chunks were filtered, for which `source_id`) — not surfaced to the end user, but available in the audit trail.
- A permission-matrix test (US-015) confirms zero over-exposure: a restricted chunk is never returned for an identity without access.
- The PermissionCache is used to avoid re-checking the source IdP on every request; TTL is configurable (default: 5 minutes for PI-1).
- If the PermissionCache entry is expired, a re-verification against the source IdP is triggered before returning results.

---

## Functional Requirements

- FR-006 (Permission-aware retrieval) — the core implementation.

---

## Non-Functional Requirements

- NFR-002 (Security) — the permission check is in the retrieval tier only; the agent tier does not and cannot call the permission check directly.
- NFR-004 (Compliance) — permission filter decisions are logged in `EvidenceItem` records (filtered chunks logged with `used_in_answer=False` and a `permission_denied` flag).

---

## Dependencies

- US-004 complete (permission enforcement design reviewed and approved by ARB).
- US-008 complete (hybrid retrieval endpoint — the filter inserts into this pipeline).
- US-005 complete (PermissionCache table exists in the database — add a new Alembic migration if not yet present).

---

## Assumptions

- `permissions_ref` on each `Chunk` record (stored at ingestion time by US-006/US-007) is a JSON structure: `{"visibility": "private"|"public", "allowed_identities": ["user1@org.com", ...], "allowed_groups": ["team-a", ...]}`.
- `requester_identity` is a validated JWT claim (email or user ID) passed from the interface tier; not caller-supplied free text.
- For PI-1: group membership is not resolved dynamically — the allowed identity list must include the specific user identity. Group-based RBAC is a PI-2 extension.
- PermissionCache TTL default: 5 minutes. After expiry, re-verify against the source system API.

---

## Edge Cases

- **All chunks filtered (requester has no access to any retrieved content):** Return `{"evidence": [], ...}` with `X-VigilRAG-Info: all-results-filtered-by-permission`; do not reveal that results exist.
- **PermissionCache expired and source IdP unreachable:** Fail-closed: treat as no access; return no results rather than serving potentially unauthorised content. Log the IdP unreachability.
- **`permissions_ref` is null/missing on a chunk:** Treat as restricted (fail-closed); log a data quality warning.
- **`requester_identity` is missing from the request:** Return HTTP 401 without processing the query at all.

---

## Technical Notes / Implementation Considerations

- **Filter location:** After RRF merge in `backend/app/routers/knowledge.py`; before returning results.
- **PermissionCache table:** `(id, requester_identity, source_id, access_level, cached_at, ttl_seconds)`; look up by `(requester_identity, source_id)`.
- **Cache miss / expiry flow:** Call the source system's permission API (GitHub repo collaborator check / Confluence space member check); store result in `PermissionCache`; apply filter.
- **`permission_denied` logging:** Add a `permission_denied: bool` field to the `EvidenceItem` record for filtered chunks; write these to the DB for audit purposes.
- **PI-1 simplification:** Check `requester_identity in chunk.permissions_ref["allowed_identities"]` or `chunk.permissions_ref["visibility"] == "public"`. Group resolution deferred to PI-2.

---

## Definition of Done

- [x] Permission filter implemented in the retrieval endpoint (post-RRF, pre-return).
- [x] PermissionCache table created (Alembic migration `0002_permission_cache`).
- [x] Cache hit, cache miss (re-verify), and cache expiry (fail-closed) all tested.
- [x] `permissions_ref` null/missing treated as restricted (fail-closed).
- [x] `requester_identity` missing → HTTP 401.
- [x] `permission_denied` flag / logger audit tracking for filtered chunks.
- [x] All-results-filtered response returns empty evidence list (`X-VigilRAG-Info: all-results-filtered-by-permission`).
- [x] Security review sign-off before any real source content is indexed against this implementation (ADR-001 approved).
- [x] CI passes with permission filter unit tests.


---

## Priority

**High** — Hard security gate; no real content may be indexed until this is implemented and reviewed.

## Estimated Effort

**L (Large)** — ~5–8 days (filter implementation, PermissionCache, IdP re-verification, audit logging, unit tests, security review).

## Related Epics / Features

- FEAT-06 (Permission-aware retrieval)
- FEAT-11 (Platform hardening — security slice)
- [Compliance & Security Framework §2](../../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md)
