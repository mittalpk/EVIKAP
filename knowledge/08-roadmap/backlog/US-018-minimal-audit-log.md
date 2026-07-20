# US-018 — Minimal Audit Log — Query, Identity, Evidence, Answer

## User Story

**As a** Compliance Officer,  
**I want to** retrieve a complete audit record for any past query — including who asked it, when, what evidence was retrieved, and what answer was given — without engineering assistance,  
**So that** EVIKAP's AI activity is auditable for internal compliance review and any applicable regulatory inquiry.

---

## Description

This story builds the compliance-facing interface to the `Query`, `EvidenceItem`, and `Answer` records persisted in US-013. It provides a read-only audit log API endpoint and a minimal admin UI view, scoped to PI-1's "minimal audit log" requirement. The full compliance-grade retention tooling and scheduled audit reports are PI-2 extensions.

---

## Business Value

- Is a hard prerequisite for indexing any source content (even low-sensitivity pilot content): a compliance reviewer must be able to answer "what did the AI see" from the audit log alone.
- Satisfies NFR-004 (Compliance) at the PI-1 slice: sufficient for internal review of low-sensitivity pilot content.

---

## Acceptance Criteria

**Given** queries have been processed and `Query`, `EvidenceItem`, and `Answer` records have been persisted (US-013),  
**When** an admin calls `GET /api/v1/audit/queries?identity=<user>&from=<date>&to=<date>`,  
**Then:**
- A paginated list of `Query` records matching the filter is returned, each including: `query_id`, `requester_identity`, `text`, `timestamp`, `answer_text`, `citations[]`, `groundedness_score`, `guardrail_flags[]`.
- A call to `GET /api/v1/audit/queries/<query_id>` returns the full detail: the above fields plus all `EvidenceItem` records for that query (chunk_id, content_excerpt, source_url, relevance_score, used_in_answer, permission_denied).
- The endpoint is admin-only (requires `admin` role from US-016).
- The admin UI displays the audit log in a searchable, filterable table.
- A compliance reviewer can answer "what did identity X see when they asked Y on date Z" from the audit log alone.

---

## Functional Requirements

- FR-008 (Audit and access review) — this is the primary implementation.

---

## Non-Functional Requirements

- NFR-004 (Compliance) — records must be retained per the data-retention policy; the endpoint must not allow deletion of audit records.
- NFR-002 (Security) — audit endpoint is admin-only; `requester_identity` in audit records comes from the JWT, not from request parameters.

---

## Dependencies

- US-013 (EvidenceItem and Answer persistence) — the records this endpoint reads.
- US-016 (RBAC) — admin-only guard.
- US-017 (JWT auth) — `requester_identity` comes from the JWT.

---

## Assumptions

- PI-1 scope: read-only query API + basic admin UI table. Compliance-grade export (CSV/PDF), scheduled reports, and retention-policy enforcement are PI-2.
- Pagination: 50 records per page; `?page=N&per_page=50` parameters.
- Full-text search over `Query.text` field is a PI-2 feature; PI-1 supports filter by identity and date range only.

---

## Edge Cases

- **No queries in the date range:** Return an empty paginated result, not a 404.
- **Very large `EvidenceItem` list for a single query:** Cap the detail response at 50 `EvidenceItem` records; add a `truncated: true` flag if more exist.
- **Audit record for a deleted user:** Retain the record with the original `requester_identity` value (do not nullify it on user deletion).

---

## Technical Notes / Implementation Considerations

- **API endpoints:**
  - `GET /api/v1/audit/queries` — paginated, filtered by `identity` and `from`/`to` date.
  - `GET /api/v1/audit/queries/{query_id}` — full detail with `EvidenceItem[]`.
- **Admin UI:** An `AuditLog` page in the frontend (`frontend/src/pages/AuditLog.tsx`) — a table of queries with a drill-down row/modal showing evidence items.
- **ORM query:** `SELECT * FROM queries WHERE requester_identity = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT 50 OFFSET ?`.
- **No DELETE or UPDATE endpoints** — the audit API is intentionally read-only.

---

## Definition of Done

- [ ] `GET /api/v1/audit/queries` and `GET /api/v1/audit/queries/{query_id}` implemented and admin-only.
- [ ] Pagination (50 per page) and date-range / identity filters working.
- [ ] `EvidenceItem[]` returned in detail view.
- [ ] `AuditLog` frontend page implemented.
- [ ] Unit tests: pagination, filter, admin guard, empty result.
- [ ] Manual test: compliance reviewer can answer "what did user X see on date Y" from the UI alone.
- [ ] Execution Runbook §4.6 (audit log bullet) marked `[x]`.
- [ ] CI passes.

---

## Priority

**High** — Required before any real content is indexed (NFR-004 compliance gate).

## Estimated Effort

**M (Medium)** — ~3–4 days (API endpoints, frontend table, unit tests).

## Related Epics / Features

- FEAT-08 (Audit and access review)
- NFR-004 (Compliance)
- Execution Runbook §4.6
