# US-012 — Citation Rendering — Inline Source Links per Answer Claim

**Status:** Completed & Archived · 2026-07-24

## User Story


**As a** Knowledge Worker,  
**I want to** see which specific source document or code file each part of the answer comes from, displayed as numbered inline citations with clickable links,  
**So that** I can verify the answer against the original source and trust the platform enough to rely on it without double-checking elsewhere.

---

## Description

Citations are the primary trust mechanism in VigilRAG. This story ensures that the UI renders citations in a format that is clear, scannable, and directly actionable — each citation links to the original source, identifies the source type, and shows a brief excerpt from the retrieved chunk. This is what differentiates VigilRAG from a black-box LLM response: every claim is traceable.

Note: this story focuses on the UI rendering. The citation data structure is assembled by the agent tier (US-011) and carried in the API response. This story does not change the backend.

---

## Business Value

- Trust cannot be validated in the MVP without visible citations — this is explicitly named as non-negotiable in [MVP Definition §3](../../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp).
- Directly addresses the VigilRAG audit finding: "citation discipline not enforced" in the current system.

---

## Acceptance Criteria

**Given** the API returns an answer with a citations list containing at least one `EvidenceItem`,  
**When** the answer is rendered in the UI,  
**Then:**
- Each citation is displayed as a numbered superscript `[1]`, `[2]`, etc., inline within the answer text where possible, or as a numbered list below the answer if inline placement is not feasible.
- Each citation entry in the list shows: source type badge (GitHub repo / Wiki), file or page name, a ≤3-line excerpt from the chunk content, and a clickable link to the original source URL.
- Citations are visually distinct from the main answer text (e.g., a lighter background, bordered section).
- If a citation URL is not accessible (broken link), the citation still renders with the file name and excerpt; the link shows a "Source may be restricted" notice.
- The citation list is collapsible to reduce visual clutter on long answers.
- `guardrail_flags` (if non-empty) are displayed as a warning banner above the answer: "This response was modified by safety guardrails."

---

## Functional Requirements

- FR-003 (Provenance and citation) — the core implementation of this requirement on the frontend.
- FR-012 (Guardrails) — `guardrail_flags` display.

---

## Non-Functional Requirements

- NFR-006 (Performance) — citation rendering is client-side only; no additional API calls for citation display.

---

## Dependencies

- US-010 (Query Submission UI) — the answer display component exists.
- US-011 (API Query Endpoint) — the `citations[]` field is present in the API response.

---

## Assumptions

- The `EvidenceItem` structure returned by the API includes: `chunk_id`, `source_url`, `source_type` (enum: `github` / `wiki`), `content_excerpt` (≤200 chars), `relevance_score`.
- Inline citation placement (superscripts within the answer text) requires the backend to return answer text with numbered citation markers. If the LLM does not include markers, citations are displayed as a footnote-style list below the answer only.
- Source URL links open in a new browser tab.

---

## Edge Cases

- **No citations returned (empty `citations[]`):** Display a warning: "⚠ No sources found. This answer may be ungrounded — verify independently."
- **More than 10 citations:** Show the first 5 expanded, with a "Show N more sources" toggle.
- **Citation URL is a GitHub file link that requires authentication:** Display the file path and excerpt; add a note "Sign in to GitHub to view the full source."
- **`guardrail_flags` contains `"pii-redacted"`:** Show: "PII has been redacted from this response."

---

## Technical Notes / Implementation Considerations

- **Component:** `CitationList` component in `frontend/src/components/CitationList.tsx`.
- **Source type badge:** A small icon + label component. GitHub = `<GitBranch />` icon; Wiki = `<BookOpen />` icon (from `lucide-react` or equivalent).
- **Collapsible:** Use a `<details>/<summary>` element or a toggle button; the collapsed state shows citation count ("3 sources").
- **Inline markers:** If the LLM places `[1]`, `[2]` markers in the answer text, use a regex post-process to replace them with `<sup>` elements linked to the citation list entry.
- **`guardrail_flags` banner:** A styled `<div role="alert">` with a ⚠ icon and a message per flag type. Map known flag values to human-readable messages.

---

## Definition of Done

- [x] `CitationList` component implemented, rendering citation number, source type badge, file name, excerpt, and clickable URL (`frontend/src/CitationList.tsx`).
- [x] Inline superscript markers supported (regex replacement in answer text).
- [x] Collapsible citation list with count toggle.
- [x] Empty citations warning rendered correctly.
- [x] `guardrail_flags` banner rendered for non-empty flag lists.
- [x] Broken/restricted URL handling confirmed.
- [x] Component unit tests (React Testing Library): normal case, empty citations, many citations, guardrail flag (`frontend/src/CitationList.test.tsx`).
- [x] CI frontend validate job passes (`npm test` & `npm run build`).


---

## Priority

**High** — Non-negotiable MVP requirement for user trust validation.

## Estimated Effort

**S (Small)** — ~1–2 days (component, tests; builds directly on the US-010 display layer).

## Related Epics / Features

- FEAT-03 (Provenance and citation)
- FEAT-17 (Guardrails — `guardrail_flags` display)
