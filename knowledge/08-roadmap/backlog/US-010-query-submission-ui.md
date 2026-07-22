# US-010 — Query Submission UI — Basic Input & Response Display

## User Story

**As a** Knowledge Worker (pilot user),  
**I want to** type a natural-language question into the VigilRAG web interface and receive a synthesised answer with clearly displayed source citations,  
**So that** I can get a trustworthy, traceable answer without navigating multiple disconnected systems.

---

## Description

This story implements the human-facing query interface (FR-001): a text input, a submit button, a loading state, an answer display area, and a citation list. It connects to the backend query endpoint (US-011) and renders the structured response. This is the surface that pilot users will interact with — it must be clear, trustworthy-feeling, and not require any technical onboarding.

---

## Business Value

- Delivers the primary user-facing MVP capability.
- The visual design of citations and source attribution directly impacts the perceived trustworthiness that the MVP hypothesis requires ≥60% users to achieve.
- Enables the concierge-to-automated transition: pilot users previously answered via the manual concierge (US-003) can now use the real system.

---

## Acceptance Criteria

**Given** the frontend is loaded in a browser and the backend is running,  
**When** a user types a question in the query input and clicks "Ask" (or presses Enter),  
**Then:**
- A loading indicator is shown while the request is in flight.
- The synthesised answer is displayed in a readable format (Markdown rendering supported).
- Each citation is displayed below the answer as a clickable link to the source (file path or URL) with the source type (GitHub / Wiki) indicated.
- If the backend returns an error, a user-friendly error message is displayed (not a raw stack trace).
- The UI is responsive and usable on desktop browsers (Chrome, Firefox, Edge latest versions).
- The query input is cleared or retained after submission (design decision: retain for follow-up queries).
- A unique `trace_id` from the response is displayed in a collapsible "Debug / Trace" section (for platform engineers, not visible by default to end users).

---

## Functional Requirements

- FR-001 (Unified query interface — UI).
- FR-003 (Provenance and citation — rendered per claim/source in the response).

---

## Non-Functional Requirements

- NFR-006 (Performance) — the UI must show the loading indicator within 100ms of submit; no perceived hang before the backend response arrives.
- NFR-008 (Availability) — the frontend must handle backend unavailability gracefully (show error state, not a broken page).

---

## Dependencies

- US-011 (API query endpoint) implemented and accessible from the frontend.
- US-012 (citation rendering) can be implemented as part of this story or as a close follow-on; the UI must at minimum display source URLs.

---

## Assumptions

- The frontend is the existing React 18 + TypeScript + Vite application in `frontend/`.
- Citations are returned by the backend as structured `EvidenceItem` objects with `source_url` and `source_type`.
- Authentication UI (login flow) exists or is mocked with a hardcoded test token for PI-1; full RBAC UI is a PI-2 concern.
- Markdown rendering uses a library already available or easily added (e.g., `react-markdown`).

---

## Edge Cases

- **Backend returns an empty evidence list:** Display the answer (if any) with a notice: "No sources found for this query. Answer may be ungrounded."
- **Backend returns an error (5xx):** Show "Something went wrong. Please try again." with a retry button.
- **Very long answer with many citations:** The UI must handle this gracefully — scroll within the answer area rather than breaking the layout.
- **User submits an empty query:** Disable the submit button when input is empty; show a validation message if submitted via keyboard shortcut.
- **Network timeout (backend takes > 10 seconds):** Show an inline timeout warning; allow the user to cancel and resubmit.

---

## Technical Notes / Implementation Considerations

- **Component structure:** `QueryInput`, `AnswerDisplay`, `CitationList`, `LoadingIndicator` — four focused components.
- **API call:** Use `frontend/src/api/client.ts`; add a `postQuery(query: string, identity: string): Promise<QueryResponse>` function.
- **`QueryResponse` type:** `{ answer: string; citations: EvidenceItem[]; trace_id: string; guardrail_flags?: string[] }`.
- **Markdown rendering:** Add `react-markdown` if not already present.
- **Citation display:** Each citation as a chip or numbered footnote with: source type icon (GitHub/Wiki), file/page name, clickable URL. Consistent with the structured citation format defined in US-012.
- **Trace ID section:** Collapsed `<details>` element below the answer; shows `trace_id` and response time.
- **Auth stub for PI-1:** Pass a hardcoded `X-User-Identity` header from the frontend; real JWT integration comes with US-017.

---

## Definition of Done

- [ ] Query input + submit interaction works end-to-end (frontend → US-011 API → answer display).
- [ ] Loading state displayed during request.
- [ ] Answer rendered as Markdown.
- [ ] Citations displayed as clickable source links with source type indicated.
- [ ] Error state handled (backend error + network timeout).
- [ ] Empty query validation.
- [ ] `trace_id` visible in collapsed debug section.
- [ ] Responsive layout confirmed on desktop browsers (Chrome, Firefox, Edge).
- [ ] Component unit tests (React Testing Library): input, submit, loading, answer, citations, error.
- [ ] CI (`ci.yml` frontend validate job) passes.

---

## Priority

**High** — Primary user-facing MVP surface.

## Estimated Effort

**M (Medium)** — ~3–5 days (components, API integration, tests, UX polish).

## Related Epics / Features

- FEAT-01 (Unified query interface)
- FEAT-03 (Provenance and citation — display layer)
