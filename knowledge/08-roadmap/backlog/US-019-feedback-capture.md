# US-019 — Thumbs Up / Down Feedback Capture

## User Story

**As a** Knowledge Worker (pilot user),  
**I want to** rate each answer I receive with a thumbs up or thumbs down directly in the query interface,  
**So that** I can quickly signal whether the answer was useful, and the platform can use that signal to improve retrieval quality over time.

---

## Description

This is the minimal feedback capture described in [MVP Definition §3](../../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp) and FR-009. The thumbs up/down captures the cheapest possible quality signal per answered query. The routing of this feedback into the evaluation dataset pipeline is the responsibility of US-020; this story is only the capture mechanism.

---

## Business Value

- Gives pilot users an active role in improving the platform — which itself increases adoption and engagement.
- Seeds the evaluation dataset with real user quality signals, reducing reliance on the manually-curated golden dataset alone.

---

## Acceptance Criteria

**Given** a query has been answered and displayed in the UI,  
**When** the user clicks the 👍 or 👎 button,  
**Then:**
- A `POST /api/v1/feedback` request is sent with: `query_id`, `rating` (`positive` / `negative`), `requester_identity` (from JWT), and an optional free-text `comment` field (max 500 chars).
- The response returns HTTP 200 with a `{"received": true}` acknowledgement.
- The feedback record is persisted to a `feedback` table in the database.
- The UI shows a brief confirmation ("Thanks for your feedback!") and disables the feedback buttons for that query (one rating per query per user).
- A negative rating optionally surfaces a text field: "What was wrong with this answer?" (optional; max 500 chars).

---

## Functional Requirements

- FR-009 (Feedback and correction loop — capture step).

---

## Non-Functional Requirements

- NFR-006 (Performance) — feedback submission must not block the UI; fire-and-forget async POST.
- NFR-003 (Privacy) — `comment` text must not contain PII; apply a basic PII check (Presidio, once US-026 is available) before persisting; for PI-1, log a warning if the comment appears to contain an email address (simple regex).

---

## Dependencies

- US-010 (Query Submission UI) — the feedback buttons are added to the answer display.
- US-011 (API Query Endpoint) — `query_id` is available from the response.
- US-017 (JWT auth) — `requester_identity` from the JWT.

---

## Assumptions

- One rating per (`query_id`, `requester_identity`) pair — prevent multiple submissions for the same query.
- Free-text comment is optional; the thumbs rating alone is sufficient for the evaluation dataset signal.
- The `feedback` table is a new Alembic migration in this story.

---

## Edge Cases

- **User submits feedback twice for the same query:** Return HTTP 409 "Feedback already submitted for this query." Update the existing record only if the rating changed (not a new record).
- **Backend unavailable when user clicks feedback:** Show a toast "Feedback couldn't be saved — please try again." Do not lose the feedback silently.
- **`query_id` not found in the database:** Return HTTP 404; the UI should not surface this to the user (log it server-side).

---

## Technical Notes / Implementation Considerations

- **DB table:** `feedback (id, query_id FK, requester_identity, rating ENUM('positive','negative'), comment TEXT, submitted_at)`.
- **API endpoint:** `POST /api/v1/feedback` — authenticated (requires valid JWT), not admin-only.
- **UI component:** Add a `FeedbackBar` component below the `AnswerDisplay` in US-010; two icon buttons (👍 / 👎); on click, show optional comment field; on submit, show confirmation toast.
- **Uniqueness constraint:** `UNIQUE(query_id, requester_identity)` in the DB table; handle the DB constraint error in the API (return 409).
- **PI-1 PII check:** Regex `r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'` on `comment`; log a warning if detected; do not reject the submission (full Presidio integration is US-026).

---

## Definition of Done

- [ ] `feedback` table created via Alembic migration.
- [ ] `POST /api/v1/feedback` endpoint implemented, authenticated, and handles duplicate submissions (409).
- [ ] `FeedbackBar` UI component implemented with thumbs buttons, optional comment, confirmation toast.
- [ ] One-rating-per-query-per-user enforced in UI and API.
- [ ] Basic PII regex check on comment text.
- [ ] Unit tests: valid feedback, duplicate submission, missing `query_id`.
- [ ] CI passes.
- [ ] Execution Runbook §4.6 (feedback capture bullet) updated toward `[x]`.

---

## Priority

**Medium** — Important for evaluation dataset bootstrapping but does not block pilot go-live.

## Estimated Effort

**S (Small)** — ~1–2 days (DB table, API endpoint, UI component, tests).

## Related Epics / Features

- FEAT-09 (Feedback and correction loop — capture)
- Execution Runbook §4.6
