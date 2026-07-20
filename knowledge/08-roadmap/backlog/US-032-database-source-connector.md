# US-032 — Structured/Database Source Connector (Postgres Schema)

## User Story

**As a** Platform Engineer,  
**I want to** implement a database source connector that connects to a Postgres database, extracts table schemas and key metadata, generates embeddings for schema descriptions, and makes that structured knowledge searchable in the retrieval endpoint,  
**So that** users can ask questions like "what tables track customer orders?" and receive answers drawn from real database schema knowledge.

---

## Description

This story closes the most prominent dishonesty in the original EVIKAP implementation: `DatabaseSubsystem.query_schemas()` performs a GitHub filename search and returns fake "schema" results. This story replaces it with a real database connector that: connects to a Postgres source (read-only), introspects schemas/tables/columns/comments, creates meaningful text representations of each table/column, and ingests them as `Chunk` records with embeddings — using the same ingestion pipeline as US-006/US-007.

---

## Business Value

- Closes the "fictional database layer" finding in the EVIKAP audit — the most damaging credibility gap.
- Enables a new class of questions (schema discovery, data lineage) that code + wiki retrieval cannot answer.

---

## Acceptance Criteria

**Given** a Postgres database is registered as a `Source` in the source registry (US-031),  
**When** the database connector ingestion pipeline runs,  
**Then:**
- Table schemas (table name, column names, data types, constraints, comments) are extracted using `information_schema` queries (read-only; no DML access).
- Each table is represented as a `Chunk` with content: a structured text description including table name, column definitions, and any available column comments.
- Embeddings are generated and stored in the `Chunk.embedding` column.
- `parent_doc_id` is set to the schema-level document ID (one schema = one parent document).
- `permissions_ref` captures the database user's access level (which schemas/tables they can query).
- The retrieval endpoint returns database schema chunks alongside code and wiki chunks for relevant queries.
- A query like "what tables track customer orders?" returns the relevant table schema chunk in top-5 results.

---

## Functional Requirements

- FEAT-12 (Structured/database source connector — extends FR-002 scope).
- FR-006 (Permission-aware retrieval — `permissions_ref` for database schemas).

---

## Non-Functional Requirements

- NFR-002 (Security) — database credentials stored in secrets manager; connector uses a read-only database user (`GRANT SELECT ON information_schema` only).
- NFR-010 (Maintainability) — connector reuses the shared ingestion utilities from US-006/US-007 (`backend/app/ingestion/utils.py`).

---

## Dependencies

- US-005 (Live Postgres + pgvector database for storing chunks).
- US-006/US-007 (Shared ingestion utilities).
- US-031 (Source registration — database sources registered through the admin workflow).
- US-008 (Hybrid retrieval endpoint — database chunks searchable alongside other sources).

---

## Assumptions

- The target database is Postgres (same as the EVIKAP data store or a separate source database).
- Read-only access via a dedicated service account with `GRANT SELECT ON ALL TABLES IN SCHEMA information_schema`.
- Schema introspection uses `SELECT table_name, column_name, data_type, is_nullable, column_default FROM information_schema.columns`.
- Table/column comments are extracted via `pg_description` joined to `pg_class` / `pg_attribute`.
- One `Chunk` per table (not per column); column details are included in the chunk's text content.

---

## Edge Cases

- **Database has thousands of tables:** Chunk by schema (one chunk per table); the embedding model context window is sufficient for a single table's column list. If a table has > 100 columns, truncate the chunk to the first 100 columns and log a warning.
- **No column comments available:** Include schema-only information (table name, column names, data types); do not fabricate descriptions.
- **Connection refused (source DB unavailable during ingestion):** Fail the ingestion run gracefully; log the error; do not mark the source as `error` until 3 consecutive failures.

---

## Technical Notes / Implementation Considerations

- **Implementation location:** `backend/app/ingestion/database_connector.py`.
- **Introspection query:**
  ```sql
  SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    col_description(pgc.oid, c.ordinal_position) AS column_comment
  FROM information_schema.tables t
  JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
  LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
  WHERE t.table_schema = $schema AND t.table_type = 'BASE TABLE'
  ORDER BY t.table_name, c.ordinal_position;
  ```
- **Chunk text format:**
  ```
  Table: orders (schema: public)
  Description: [table comment if available]
  Columns:
    - id: bigint, NOT NULL, PK
    - customer_id: bigint, NOT NULL, FK → customers.id
    - created_at: timestamp, NOT NULL
    - status: varchar(50), NOT NULL
  ```
- **`permissions_ref`:** `{"schema": "public", "database_user": "<connector_user>", "access": "read-only"}`.

---

## Definition of Done

- [ ] `backend/app/ingestion/database_connector.py` implemented.
- [ ] Schema introspection with column comments working.
- [ ] Chunk text format clear and embedding-ready.
- [ ] `permissions_ref` captures database access level.
- [ ] Database chunks retrievable via US-008 hybrid retrieval endpoint.
- [ ] Integration test: schema chunks ingested; query "what tables track customer orders?" returns relevant chunk in top-5.
- [ ] Old `DatabaseSubsystem.query_schemas()` removed.
- [ ] Unit tests: introspection mock, chunk text formatting, upsert.
- [ ] CI passes.

---

## Priority

**High** in PI-2 (FEAT-12 is a "Should" / PI-2 objective).

## Estimated Effort

**M (Medium)** — ~3–5 days (connector, introspection query, chunk formatter, tests; reuses ingestion utilities).

## Related Epics / Features

- FEAT-12 (Structured/database source connector)
- FR-002 (Cross-source semantic retrieval — extended to DB schemas)
