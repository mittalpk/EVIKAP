# US-039 — Full Compliance-Grade Audit Log — Retention, Export & Scheduled Reports

## User Story

**As a** Compliance Officer,  
**I want to** enforce automated data retention on audit records, export audit logs in compliance-grade formats (CSV/PDF) for regulatory submissions, and receive scheduled audit digest reports,  
**So that** VigilRAG's audit log is sufficient for regulated-data source onboarding and any applicable external regulatory inquiry — not just internal pilot review.

---

## Description

US-018 delivered the PI-1 minimal audit log: a read-only query API and a basic admin UI table. This PI-2 story completes FEAT-08 by adding the compliance-grade capabilities explicitly deferred from PI-1: automated retention-policy enforcement, export, scheduled reports, and full-text search over query history. These capabilities are required before any regulated-data source (sensitivity class "internal-sensitive" or above) can be onboarded per [Compliance & Security Framework §3](../../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md#3-regulated-data-onboarding-prerequisites).

---

## Business Value

- Enables regulated-data source onboarding — currently blocked by the absence of compliance-grade audit tooling.
- Satisfies NFR-004's full verification clause: "compliance sign-off on audit log schema and retention period" required by the Compliance & Security Framework.
- Replaces manual compliance review ("engineer pulls a DB query") with a self-service compliance tooling suite.

---

## Acceptance Criteria

**Given** the audit retention policy is configured (e.g., `AUDIT_RETENTION_DAYS=365`),  
**When** audit records exceed the retention period,  
**Then:**
- Records older than the retention period are archived (moved to a cold-storage table or exported and deleted from the hot table) — not hard-deleted without an archival step.
- A retention job run log is created for each execution.

**Given** a compliance reviewer requests an audit export,  
**When** they call `POST /api/v1/audit/export?from=<date>&to=<date>&format=csv`,  
**Then:**
- A CSV or PDF export file is generated containing all `Query` + `EvidenceItem` + `Answer` records for the date range.
- The export is admin-only and the download URL expires after 1 hour.
- Export generation and download are logged in the audit trail (meta-audit).

**Given** scheduled reports are configured,  
**When** the weekly/monthly report job runs,  
**Then:**
- A digest report (summary statistics: query count, unique identities, flagged responses, guardrail events) is emailed/Slacked to the configured Compliance Officer distribution list.

---

## Functional Requirements

- FR-008 (Audit and access review — FEAT-08 PI-2 slice).

---

## Non-Functional Requirements

- NFR-004 (Compliance) — the full verification: compliance sign-off on the complete audit schema and retention period before regulated-data source onboarding.
- NFR-002 (Security) — export download links must be time-limited (signed URLs or short-TTL tokens); meta-audit logs every export action.

---

## Dependencies

- US-018 (Minimal audit log — the records and API this story extends).
- US-035 (Terraform network drift — network isolation required for regulated-data source onboarding).
- US-016/US-017 (RBAC and JWT auth — export endpoint admin-only).

---

## Assumptions

- Cold-storage archive: a separate `archived_queries` table in the same Postgres instance (not an external object store) for PI-2; S3/Blob archival is a future hardening.
- PDF export uses a Python PDF library (`reportlab` or `weasyprint`); CSV is stdlib.
- Scheduled reports use the same cron mechanism as the feedback routing job (US-020).
- The Compliance Officer's email/Slack is configurable via an admin settings page (not hardcoded).

---

## Edge Cases

- **Retention job fails mid-run:** Do not partially archive; wrap the archival batch in a DB transaction. Log the failure and retry at the next scheduled run.
- **Export request for a very large date range (millions of records):** Return a 202 Accepted response; generate the export asynchronously; notify the requester by email when ready.
- **Meta-audit logging fails:** Log the failure to the application log but do not block the export action; surface a warning on the admin dashboard.

---

## Technical Notes / Implementation Considerations

- **Retention job:** `scripts/enforce_audit_retention.py` — scheduled nightly; selects `Query` records where `timestamp < NOW() - INTERVAL '<AUDIT_RETENTION_DAYS> days'`; inserts into `archived_queries`; deletes from `queries` (cascade deletes `evidence_items` and `answers`).
- **Export API:** `POST /api/v1/audit/export` — accepts `from`, `to`, `format` (`csv`/`pdf`); generates the file; returns a signed download URL (expires in 3600 seconds).
- **PDF format:** Each page covers one query: identity, timestamp, full answer text, evidence items as a table, guardrail flags.
- **Scheduled digest report:** `scripts/send_audit_digest.py` — reads aggregate stats for the past week/month; renders a Markdown/HTML summary; sends via the configured email/Slack integration.
- **Full-text search:** Add a GIN index on `queries.text` (`CREATE INDEX ON queries USING GIN(to_tsvector('english', text))`); expose `?q=<search_term>` on the audit list endpoint.
- **Compliance sign-off checklist:** A formal sign-off document (Markdown) filed in `knowledge/07-governance-risk/` confirming schema + retention period + export capability are reviewed and accepted.

---

## Definition of Done

- [ ] Retention enforcement job implemented and scheduled; tested with a fixture dataset.
- [ ] Cold-storage archival transactional (no partial archival on failure).
- [ ] `POST /api/v1/audit/export` endpoint implemented (CSV and PDF); admin-only.
- [ ] Export download URL time-limited (1-hour TTL).
- [ ] Export action logged in the audit trail (meta-audit).
- [ ] Async export for large date ranges (202 + email notification).
- [ ] Weekly/monthly digest report configured and sending to the Compliance Officer distribution list.
- [ ] Full-text search (`?q=`) on the audit list endpoint implemented.
- [ ] Compliance sign-off document filed in `knowledge/07-governance-risk/`.
- [ ] Regulated-data source onboarding gate: Compliance & Security Framework §3 prerequisites confirmed met.
- [ ] CI passes.

---

## Priority

**High** in PI-2 — prerequisite for regulated-data source onboarding.

## Estimated Effort

**L (Large)** — ~5–8 days (retention job, export API, PDF generation, digest reports, full-text search, compliance sign-off process).

## Related Epics / Features

- FEAT-08 (Audit and access review — PI-2 full compliance-grade slice)
- NFR-004 (Compliance)
- [Compliance & Security Framework §3](../../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md)
