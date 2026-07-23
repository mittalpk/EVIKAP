# US-006 — GitHub Source Connector — Embedding Ingestion Pipeline

**Status:** Completed & Archived · **Date:** 2026-07-23  
**Connector Module:** `backend/app/services/github_connector.py`  
**Test Suite:** `backend/tests/test_github_connector.py`  

## User Story

**As a** Platform Engineer,  
**I want to** implement an ingestion pipeline that fetches files from a configured GitHub repository, splits them into chunks, generates embeddings using the configured embedding model, and stores the resulting `Chunk` records (with `parent_doc_id`, `references`, and `embedding`) in the Postgres + pgvector database,  
**So that** GitHub repository content is searchable via semantic vector similarity in the retrieval endpoint (US-008).

---

## Description

This story replaces `GitHubSearchSubsystem`, which currently performs substring/keyword filename matching and returns raw GitHub API results. The new pipeline performs real embedding-based ingestion: fetch → chunk → embed → store. The chunking must preserve Graph-Ready metadata (`parent_doc_id` for file → section hierarchy, `references` for import/include relationships extracted from the code). Permissions metadata (`permissions_ref`) from the source system must be captured and stored alongside each chunk so that FR-006 (permission-aware retrieval in US-014) can use it without re-fetching.

---

## Business Value

- Replaces the core weakness identified in the VigilRAG audit: keyword-only retrieval masquerading as semantic search.
- Enables meaningful, meaning-based code search — the highest-value source type per the pilot problem validation.

---

## Acceptance Criteria

**Given** a GitHub repository is registered as a `Source` in the database (with connection credentials in Key Vault / secrets),  
**When** the ingestion pipeline runs (manually triggered or scheduled),  
**Then:**
- All files matching the configured scope (e.g., `*.py`, `*.md` within a path filter) are fetched via the GitHub API.
- Each file is split into chunks with configurable overlap (default: 512 tokens, 50-token overlap).
- Each chunk has `parent_doc_id` set to the originating file's document ID.
- Import/include statements in code files are parsed and written to the `references` field.
- An embedding vector is generated for each chunk using the configured embedding model (`text-embedding-004` or equivalent).
- The `Chunk` record is upserted (update if checksum unchanged, replace if changed) in the database.
- `Source.last_indexed_at` is updated on completion.
- The pipeline respects GitHub API rate limits (does not exhaust the token's rate budget in a single run).
- A run summary is logged (files fetched, chunks created, chunks updated, errors).

---

## Functional Requirements

- FR-002 (Cross-source semantic retrieval) — embedding ingestion is the prerequisite for semantic retrieval.
- FR-005 (Freshness) — `checksum` and `last_indexed_at` per chunk enable the freshness detection mechanism.
- FR-006 (Permission-aware retrieval) — `permissions_ref` must be stored per chunk at ingestion time (not looked up at query time from scratch).

---

## Non-Functional Requirements

- NFR-002 (Security) — GitHub credentials/tokens must be read from the secret store; never hardcoded or logged.
- NFR-010 (Maintainability) — the connector must be independently deployable and testable; mock the GitHub API in unit tests.
- NFR-006 (Performance) — ingestion should be async and batch-processable; avoid blocking the backend API process.

---

## Dependencies

- US-005 complete (live Postgres + pgvector target available).
- US-004 complete (permission enforcement design — `permissions_ref` schema agreed).
- Embedding model API key configured in secrets.
- `backend/app/models.py` (`Source`, `Chunk`) already implemented in `feature/data-layer-supabase`.

---

## Assumptions

- GitHub repository is accessible via the GitHub REST API v3 using a fine-grained personal access token with `contents: read` scope.
- Chunking at 512 tokens with 50-token overlap is a reasonable starting point; can be tuned post-ingestion based on retrieval quality metrics (US-009).
- Import/reference extraction is best-effort (regex-based for MVP); full AST parsing is a future improvement.
- The embedding model API is available and its cost is acceptable for the pilot corpus size.

---

## Edge Cases

- **File too large to fit in a single embedding API call:** Split into sub-chunks; each sub-chunk references the same `parent_doc_id`.
- **GitHub API rate limit hit mid-ingestion:** Pause, log the rate-limit reset time, resume after the window. Do not lose partially-ingested runs (use a checkpoint or idempotent upsert).
- **Binary file encountered (images, PDFs, compiled artefacts):** Skip with a log entry; do not attempt to embed non-text content.
- **File deleted from repository between runs:** Mark the corresponding `Chunk` records as stale (`last_indexed_at` not updated) and set a `deleted_at` timestamp; do not serve stale chunks in retrieval.
- **Embedding API unavailable:** Fail the ingestion run gracefully; log the error; do not partially commit chunks that lack embeddings.

---

## Technical Notes / Implementation Considerations

- **Implementation location:** `backend/app/ingestion/github_connector.py` (new file).
- **Chunking library:** `langchain_text_splitters.RecursiveCharacterTextSplitter` or `tiktoken`-based splitter; choose one and document the choice.
- **Embedding model:** `google-generativeai` SDK → `text-embedding-004`; dimension 768 (matches pgvector column type).
- **Upsert logic:** Use `ON CONFLICT (source_id, checksum) DO UPDATE` or equivalent; do not duplicate unchanged chunks.
- **`permissions_ref` format:** A JSON blob containing the GitHub path + repository visibility + team access level at ingestion time. Subject to revision once the permission cache design (US-004) is finalised.
- **Triggering:** For PI-1, trigger manually via a management command or a scheduled cron job inside Docker Compose. A proper async task queue (Celery/ARQ) is a PI-2 improvement.
- **Unit tests:** Mock the GitHub API responses and the embedding API; assert correct chunking, checksum computation, and database upsert behaviour.

---

## Definition of Done

- [x] `backend/app/services/github_connector.py` implemented and reviewed.
- [x] Chunking, embedding, and upsert logic covered by unit tests (`backend/tests/test_github_connector.py`).
- [x] End-to-end integration test: run ingestion against database; confirm `Chunk` records appear with `embedding`, `parent_doc_id`, `references`, and `permissions_ref`.
- [x] Rate-limit handling tested (`test_github_api_rate_limit_handling`).
- [x] Binary/non-text file skipping confirmed (`binary_files_skipped` tracked).
- [x] Run summary log output confirmed (`IngestionSummary`).
- [x] `Source.updated_at` updated on successful run.
- [x] CI (`ci.yml`) passes with new unit tests included.
- [x] Execution Runbook §4.2 fourth bullet updated toward `[x]`.

---

## Priority

**High** — Core MVP capability; blocks US-008 (retrieval endpoint).

## Estimated Effort

**L (Large)** — ~5–8 days (connector, chunker, embedder, upsert logic, unit tests, integration test).

## Related Epics / Features

- FEAT-02 (Hybrid semantic + keyword retrieval)
- FEAT-05 (Freshness — `checksum` / `last_indexed_at` mechanism)
- FEAT-06 (Permission-aware retrieval — `permissions_ref` storage)
