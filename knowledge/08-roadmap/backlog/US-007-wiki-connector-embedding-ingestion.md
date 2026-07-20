# US-007 — Wiki Source Connector — Embedding Ingestion Pipeline

## User Story

**As a** Platform Engineer,  
**I want to** implement an ingestion pipeline for the internal wiki source (Confluence or local fallback), that fetches pages, splits them into chunks, generates embeddings, and stores `Chunk` records with Graph-Ready metadata,  
**So that** wiki content is semantically searchable alongside code content in the unified retrieval endpoint (US-008).

---

## Description

Mirrors US-006 for the wiki source type. The wiki connector fetches pages via the Confluence REST API (or the local demo fallback), applies the same chunk → embed → upsert pipeline, and stores results using the same `Chunk` schema. The key difference from the GitHub connector is the content structure: wiki pages have explicit parent-child hierarchy (space → page → child page) which maps naturally to `parent_doc_id`, and may have internal cross-page links which map to `references`.

---

## Business Value

- Completes the two-source MVP scope (code + wiki) per [MVP Definition §3](../../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp).
- Wiki content is often the highest-density source of policy, process, and decision-context knowledge — the question types most frequently asked by knowledge workers.

---

## Acceptance Criteria

**Given** a Confluence space (or local demo wiki) is registered as a `Source` in the database,  
**When** the wiki ingestion pipeline runs,  
**Then:**
- All pages within the configured space/scope are fetched and stripped of HTML/wiki markup to plain text.
- Each page is split into chunks with the same token budget as the GitHub connector.
- `parent_doc_id` is set to the parent page's document ID (page hierarchy preserved).
- Internal cross-page links are extracted and written to the `references` field.
- Embeddings are generated and stored with the same `pgvector` column as the GitHub connector.
- `permissions_ref` captures the Confluence space-level and page-level access restrictions at ingestion time.
- Run summary logged (pages fetched, chunks created, chunks updated, errors).
- Rate-limit handling is implemented for the Confluence API.

---

## Functional Requirements

- FR-002 (Cross-source semantic retrieval) — wiki embedding ingestion.
- FR-005 (Freshness) — `checksum` / `last_indexed_at` per chunk.
- FR-006 (Permission-aware retrieval) — `permissions_ref` stored per chunk.

---

## Non-Functional Requirements

- NFR-002 (Security) — Confluence API token stored in secrets manager; never logged or committed.
- NFR-010 (Maintainability) — connector independently testable; Confluence API mocked in unit tests.
- NFR-006 (Performance) — async ingestion; does not block backend API.

---

## Dependencies

- US-005 complete (live database available).
- US-004 complete (permission enforcement design, specifically for wiki space-level ACL representation).
- US-006 implemented (shared chunking/embedding utilities reused).

---

## Assumptions

- Confluence REST API v2 is available (cloud or server); or the local demo fallback (a directory of Markdown files) is used if Confluence is not accessible.
- The local demo fallback (a structured folder of `.md` files) is the accepted substitute for Confluence in the demo deployment profile.
- HTML-to-text conversion uses a library (e.g., `beautifulsoup4`) rather than regex stripping.
- Page-level access restrictions in Confluence are available via the Space Permissions API.

---

## Edge Cases

- **Confluence API unavailable (demo profile):** Fall back to the local directory-of-Markdown-files mode. Document the switch in the run log.
- **Page with no readable text content (attachment-only page):** Skip with a log entry.
- **Very deeply nested page hierarchy:** Flatten to at most 3 levels of `parent_doc_id` nesting for the MVP; log a warning if a deeper hierarchy is encountered.
- **Page edited between chunk generation runs:** Detect via checksum; re-embed only changed pages (same logic as US-006).

---

## Technical Notes / Implementation Considerations

- **Implementation location:** `backend/app/ingestion/wiki_connector.py` (new file).
- **Shared utilities:** Extract chunking and embedding utility functions into `backend/app/ingestion/utils.py` (shared with US-006's connector) to avoid duplication.
- **HTML stripping:** Use `beautifulsoup4` with `html.parser`; strip `<script>`, `<style>`, and navigation elements before text extraction.
- **`permissions_ref` for Confluence:** A JSON blob with `space_key`, `page_id`, and `access_restriction` (e.g., `"public"`, `"space-members-only"`, `"specific-groups": [...]`).
- **Local demo fallback:** Treat each `.md` file as a "page"; use the directory path as the `parent_doc_id` hierarchy.
- **Unit tests:** Mock Confluence API responses; assert correct HTML stripping, chunking, and DB upsert.

---

## Definition of Done

- [ ] `backend/app/ingestion/wiki_connector.py` implemented and reviewed.
- [ ] Shared ingestion utilities extracted to `backend/app/ingestion/utils.py`.
- [ ] Unit tests cover: HTML stripping, chunking, embedding mock, upsert, rate-limit handling.
- [ ] Integration test: run against live Supabase DB with a small demo wiki; confirm `Chunk` records with correct schema.
- [ ] `permissions_ref` captures page-level access restrictions.
- [ ] Demo-profile fallback (local Markdown directory) tested and working.
- [ ] CI passes with new unit tests.

---

## Priority

**High** — Required to complete the two-source MVP scope.

## Estimated Effort

**M (Medium)** — ~3–5 days (connector shares utilities with US-006; main effort is HTML stripping, permissions, and tests).

## Related Epics / Features

- FEAT-02 (Hybrid semantic + keyword retrieval)
- FEAT-05 (Freshness)
- FEAT-06 (Permission-aware retrieval)
