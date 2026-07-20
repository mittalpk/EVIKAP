# US-005 — Supabase/Postgres Project Provisioning & Database Migration

## User Story

**As a** Platform Engineer,  
**I want to** provision the Supabase (demo profile) or managed Azure Postgres (enterprise profile) database instance, apply the initial Alembic migration, and confirm the `Source` and `Chunk` tables exist with the correct schema,  
**So that** the embedding ingestion stories (US-006, US-007) have a working, live database target to write to, closing [ISSUE-010](../ISSUE_LOG.md#issue-010).

---

## Description

The data layer code (models, Alembic migration, async DB session) was implemented in the `feature/data-layer-supabase` branch. That work is complete locally and migration-tested against a local Docker `pgvector/pgvector:pg16` container. What remains is provisioning the actual target environment and running the migration against it. This story closes the blocked item in Execution Runbook §4.2 and makes [ISSUE-010](../ISSUE_LOG.md) fully resolved.

---

## Business Value

- Unblocks US-006 (GitHub ingestion), US-007 (wiki ingestion), and all downstream retrieval work.
- Replaces the fictional `DatabaseSubsystem.query_schemas()` keyword search with a real, live Postgres + pgvector backend.
- Demonstrates the data layer is production-ready (not just locally-tested) before any source content is indexed.

---

## Acceptance Criteria

**Given** the `feature/data-layer-supabase` branch is merged to `main`,  
**When** a Supabase project (demo) or Azure Postgres + pgvector instance (enterprise) is provisioned and `DATABASE_URL` / `DATABASE_USE_PGBOUNCER` are set as secrets,  
**Then:**
- `alembic upgrade head` runs successfully against the live target without errors.
- `Source` and `Chunk` tables exist in the target database with the schema defined in `backend/app/models.py`.
- The `vector` extension is enabled and the `embedding` column on `Chunk` uses `pgvector`.
- A basic connectivity test (Python async session, `SELECT 1`) passes from the `backend` container.
- `alembic downgrade base` followed by `alembic upgrade head` also succeeds (reversibility confirmed).
- [ISSUE-010](../ISSUE_LOG.md#issue-010) is updated to **Resolved** with the provisioning date.

---

## Functional Requirements

- Enables FR-002 (cross-source semantic retrieval) — the retrieval index requires a live vector store.
- Satisfies the data layer requirement for the `Source` and `Chunk` entities per [Data Architecture §5](../../04-solution-architecture/DATA_ARCHITECTURE.md#5-logical-data-entities-initial).
- Ensures the Chunk schema is Graph-Ready (per [Data Architecture §5.1](../../04-solution-architecture/DATA_ARCHITECTURE.md#51-future-entities--knowledge-graph-roadmap-feat-13)): `parent_doc_id` and `references[]` fields present.

---

## Non-Functional Requirements

- NFR-002 (Security) — `DATABASE_URL` must be stored as a secret (GitHub Actions secret / Azure Key Vault), never committed to source control.
- NFR-001 (Scalability) — use pgvector extension, not a workaround, so the schema does not need to change when the corpus grows.
- NFR-010 (Maintainability) — Alembic migration chain must remain clean; no manual schema edits to the live database allowed outside of Alembic.

---

## Dependencies

- `feature/data-layer-supabase` merged to `main` (models, migration, `db.py` already implemented).
- Supabase project created (demo) or Azure Postgres provisioned (enterprise) — this is the provisioning action itself.
- `DATABASE_URL` and `DATABASE_USE_PGBOUNCER` secrets registered in the target secret store.

---

## Assumptions

- Demo profile uses Supabase (free tier is sufficient for pilot-scale corpus).
- Enterprise profile uses Azure Database for PostgreSQL Flexible Server with pgvector extension enabled.
- The pgvector extension is available on the chosen instance tier without additional configuration.
- CI (`ci.yml`) continues to use `aiosqlite` (in-memory SQLite) for unit tests — only the live environment uses Postgres.

---

## Edge Cases

- **pgvector extension not available on selected Supabase tier:** Use the Supabase-provided pgvector, which is pre-installed on all Supabase projects. If unavailable, open a ISSUE_LOG entry and escalate.
- **`alembic upgrade head` fails due to connection timeout:** Check `DATABASE_USE_PGBOUNCER=true` if using Supabase's connection pooler (PgBouncer uses transaction mode, which Alembic's DDL requires to be disabled or bypassed via a direct connection string).
- **Schema drift between local test and live target:** Only Alembic is the source of truth. If the live schema diverges (e.g., from a manual edit), run `alembic stamp head` with caution after reconciliation, and log the incident.

---

## Technical Notes / Implementation Considerations

- **Connection string format for Supabase + PgBouncer:** Use the "direct connection" URL (port 5432) for migrations, and the "transaction pooler" URL (port 6543) for application reads/writes. Both are available in the Supabase project settings.
- **Alembic migration command:** `cd backend && alembic upgrade head`
- **Reversal test command:** `cd backend && alembic downgrade base && alembic upgrade head`
- **Connectivity test:** `python -c "import asyncio; from app.db import get_session; asyncio.run(next(get_session()).execute('SELECT 1'))"`
- The `DATABASE_URL` secret must be added to:
  - Local `.env` (never committed)
  - GitHub Actions secrets (`DATABASE_URL`) for any future integration tests that require a live DB
  - Azure Key Vault (enterprise profile) or Supabase project env (demo profile)

---

## Definition of Done

- [ ] Supabase project (or Azure Postgres) provisioned.
- [ ] pgvector extension confirmed enabled.
- [ ] `DATABASE_URL` and `DATABASE_USE_PGBOUNCER` set as secrets in the target store.
- [ ] `alembic upgrade head` completes successfully against the live database.
- [ ] `alembic downgrade base` + `alembic upgrade head` also succeeds.
- [ ] `Source` and `Chunk` tables exist with correct schema (including `parent_doc_id`, `references`, and `embedding` pgvector column).
- [ ] Basic connectivity test passes from `backend` container/process.
- [ ] [ISSUE-010](../ISSUE_LOG.md#issue-010) updated to **Resolved**.
- [ ] Runbook §4.2 first bullet updated from `(blocked)` to `[x]`.

---

## Priority

**High** — Blocks US-006, US-007, US-008, and all retrieval work.

## Estimated Effort

**S (Small)** — ~1–2 days (provisioning, secret wiring, migration run, verification).

## Related Epics / Features

- FEAT-02 (Hybrid semantic + keyword retrieval — data layer enabler)
- FEAT-12 (Database source connector — schema reused)
- Execution Runbook §4.2 (first bullet)
- [ISSUE-010](../ISSUE_LOG.md#issue-010)
