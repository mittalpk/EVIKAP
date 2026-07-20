# US-031 — Source Registration Self-Service Workflow (Admin UI)

## User Story

**As a** Platform Administrator,  
**I want to** register a new knowledge source (type, connection details, indexing scope, refresh cadence, sensitivity classification) through an admin UI workflow without requiring a code change,  
**So that** additional sources (e.g., a second GitHub repo, a new Confluence space) can be onboarded within one business day of administrative effort.

---

## Description

This story implements FR-007: the source registration workflow. Currently, sources are hardcoded in application configuration. This story replaces that with a database-backed `Source` registry, an admin UI form to register/edit/delete sources, and an API endpoint to manage the registry. The `Source` entity was already defined in [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial) and the table created in US-005/006's Alembic migrations.

---

## Business Value

- Enables the platform to grow beyond the two MVP pilot sources without engineering involvement.
- Satisfies FR-007 acceptance check: "a new source of an already-supported type can be onboarded through the workflow in under one business day of administrative effort."

---

## Acceptance Criteria

**Given** the admin is logged in with the `admin` role,  
**When** they navigate to the Source Management admin page and register a new Confluence space,  
**Then:**
- The form collects: source type (dropdown), display name, connection reference (URL/repo), credential reference (Key Vault secret name — not the credential itself), indexing scope (e.g., path filter), refresh cadence (daily/weekly/on-demand), and sensitivity classification.
- On save, a `Source` record is created in the database.
- The registered source appears in the source list with status `pending-first-index`.
- A "Trigger Index" button initiates the ingestion pipeline for that source (calls the management endpoint).
- The source transitions to `indexed` status after a successful ingestion run.
- An admin can deactivate a source (stops future indexing; does not delete existing chunks until a separate purge action).
- The entire registration + first-index workflow completes within one business day for a supported source type.

---

## Functional Requirements

- FR-007 (Source registration self-service workflow).
- FR-006 (Permission-aware retrieval) — sensitivity classification captured at registration time.

---

## Non-Functional Requirements

- NFR-002 (Security) — credential references (Key Vault secret names) are stored, not the credentials themselves; the actual credentials remain in the secrets manager.
- NFR-010 (Maintainability) — adding a new source type (e.g., Confluence) requires adding a connector class only; the admin UI form dynamically loads source type options from the backend.

---

## Dependencies

- US-005 (`Source` table exists in DB).
- US-006/US-007 (Ingestion pipelines — the "Trigger Index" button calls these).
- US-016 (RBAC — admin-only pages and endpoints).
- US-014 (Permission-aware retrieval — sensitivity classification from this story feeds the permission filter).

---

## Assumptions

- Supported source types for PI-2: `github`, `wiki_confluence`, `wiki_local`. Database source type (`postgres`) is FEAT-12 (US-032).
- The admin UI is a new page in the React frontend (`SourceManagement.tsx`).
- The "Trigger Index" action is a synchronous call to a management endpoint that starts an async background task; the UI polls for status updates.

---

## Edge Cases

- **Admin registers a source with invalid credentials (Key Vault secret does not exist):** Validate the secret reference at registration time (attempt a Key Vault lookup); reject with an error if the secret is not found.
- **Deactivating a source while an ingestion run is in progress:** Queue the deactivation; do not interrupt a running ingestion job.
- **Registering a duplicate source (same connection_ref already registered):** Return HTTP 409; display "This source is already registered."

---

## Technical Notes / Implementation Considerations

- **API endpoints:**
  - `GET /api/v1/admin/sources` — list all sources with status.
  - `POST /api/v1/admin/sources` — register a new source.
  - `PATCH /api/v1/admin/sources/{id}` — update a source config.
  - `POST /api/v1/admin/sources/{id}/trigger-index` — trigger an ingestion run.
  - `DELETE /api/v1/admin/sources/{id}` — deactivate (soft-delete: sets `active=false`).
- **`Source` status enum:** `pending_first_index`, `indexing`, `indexed`, `error`, `inactive`.
- **Frontend:** `SourceManagement.tsx` — a table of sources + a `SourceRegistrationForm` modal.
- **Source type options API:** `GET /api/v1/admin/sources/types` — returns the list of supported connector types; the frontend populates the dropdown from this response.

---

## Definition of Done

- [ ] Source management API endpoints implemented and admin-only.
- [ ] `SourceManagement` frontend page implemented with list, form, and trigger-index button.
- [ ] Source status transitions: `pending → indexing → indexed` (or `error`).
- [ ] Deactivation (soft-delete) implemented.
- [ ] Duplicate source registration returns HTTP 409.
- [ ] FR-007 acceptance check: a second Confluence space onboarded within one business day (manual test).
- [ ] Unit tests: CRUD operations, duplicate check, trigger-index call.
- [ ] CI passes.

---

## Priority

**Medium** (Stretch in PI-2 per PI planning objectives).

## Estimated Effort

**L (Large)** — ~5–8 days (API CRUD, frontend form + table, status management, trigger-index integration, tests).

## Related Epics / Features

- FEAT-07 (Source registration self-service workflow)
- FR-007
