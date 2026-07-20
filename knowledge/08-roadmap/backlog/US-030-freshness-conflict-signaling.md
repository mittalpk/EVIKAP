# US-030 — Freshness Detection & Conflict Signaling

## User Story

**As a** Knowledge Worker,  
**I want to** be warned when two sources disagree on the same topic or when the most relevant source appears to be stale relative to newer sources,  
**So that** I don't unknowingly rely on outdated or conflicting information in my work.

---

## Description

This story implements FR-005: detecting and surfacing freshness/conflict signals in the synthesis response. When retrieved evidence includes: (a) two chunks with similar content but contradictory facts, or (b) a chunk with an older `last_indexed_at` than another chunk on the same topic, the synthesised answer must flag this rather than silently presenting one source as authoritative.

---

## Business Value

- Prevents the platform from becoming a source of stale misinformation — a critical trust risk for knowledge workers who rely on it for decisions.
- Satisfies FR-005 acceptance check: a test fixture with two conflicting source documents produces a response that flags the conflict and cites both.
- Requires a pilot corpus large enough for conflicts to actually occur — properly sequenced to PI-2 per [MVP Definition §4](../../05-lean-product/MVP_DEFINITION.md#4-explicitly-deferred-past-mvp).

---

## Acceptance Criteria

**Given** two retrieved chunks with similar `parent_doc_id` topic tags but contradictory content (e.g., "Service A uses OAuth" vs "Service A uses API key auth"),  
**When** the agent synthesises an answer,  
**Then:**
- The synthesised answer explicitly flags the conflict: "Note: sources disagree on this topic. [Source A] states X, while [Source B] states Y."
- Both conflicting sources are cited.
- The `Answer.conflict_signal` field is set to `true`.
- Given a stale chunk (a chunk whose `last_indexed_at` is more than the configured staleness threshold — default 30 days — older than the most recent chunk on the same topic), the answer includes: "Note: [Source A] may be outdated — last updated [date]. A more recent source [Source B] may supersede it."
- A test fixture with two conflicting chunks produces the conflict signal; a test fixture with one stale chunk produces the staleness signal.

---

## Functional Requirements

- FR-005 (Freshness and conflict signaling).

---

## Non-Functional Requirements

- NFR-006 (Performance) — conflict detection runs in-memory on the retrieved evidence set; no additional DB query required.

---

## Dependencies

- US-008 (Hybrid retrieval endpoint — returns `last_indexed_at` and content per chunk).
- US-011 (API query endpoint — conflict signal passed to synthesis prompt and stored in `Answer`).
- US-006/US-007 (Ingestion — `checksum` and `last_indexed_at` must be populated per chunk).

---

## Assumptions

- Conflict detection in PI-2 is LLM-based: pass the top-k evidence list to the LLM and ask "do any of these sources contradict each other? If yes, identify the conflicting pairs." A rule-based approach (embedding similarity + topic-tag matching) is a future refinement.
- Staleness threshold: configurable via `FRESHNESS_STALENESS_DAYS` env var; default 30 days.
- `Answer` DB entity gets a new `conflict_signal: bool` and `staleness_signal: bool` field (Alembic migration).

---

## Edge Cases

- **No conflict detected but sources are genuinely contradictory (LLM missed it):** This is a quality gap, not an error. Track as a RAGAS evaluation failure; do not silence the response.
- **All sources are stale (entire corpus is old):** Flag all retrieved sources as potentially stale; include a global staleness warning in the answer.
- **Conflict signal triggered by minor wording differences (false positive):** Tune the LLM conflict-detection prompt; add false-positive examples to the conflict detection prompt as few-shot examples.

---

## Technical Notes / Implementation Considerations

- **Conflict detection prompt:** Pass the top-k evidence list as JSON to the LLM; ask "Identify any pairs of sources that appear to contradict each other. Return a JSON list of `{source_a_chunk_id, source_b_chunk_id, description}`."
- **Staleness check:** `max(last_indexed_at) - chunk.last_indexed_at > FRESHNESS_STALENESS_DAYS for chunk in evidence` — simple in-memory computation.
- **Synthesis prompt update:** If conflicts or staleness are detected, prepend a context section to the synthesis prompt: "Note: the following conflicts/staleness issues were detected in the evidence. Please surface them explicitly in the answer."
- **`Answer` schema update:** Add `conflict_signal: bool`, `staleness_signal: bool` fields via Alembic migration.
- **Fixture test:** Two Markdown fixture files with contradictory content ingested into the test DB; query produces a conflict signal.

---

## Definition of Done

- [ ] Conflict detection (LLM-based) implemented in the agent tier.
- [ ] Staleness detection (in-memory computation) implemented.
- [ ] Synthesis prompt updated to surface signals in the answer text.
- [ ] `Answer.conflict_signal` and `Answer.staleness_signal` fields added (Alembic migration).
- [ ] FR-005 fixture test: conflicting chunks → conflict flag in response; stale chunk → staleness warning.
- [ ] `FRESHNESS_STALENESS_DAYS` configurable via env var.
- [ ] Unit tests: conflict detection, staleness detection, false-positive case.
- [ ] CI passes.

---

## Priority

**Medium** (Stretch in PI-2 per PI planning objectives).

## Estimated Effort

**M (Medium)** — ~3–4 days (conflict detection prompt, staleness logic, synthesis prompt update, DB migration, fixture test).

## Related Epics / Features

- FEAT-05 (Freshness and conflict signaling)
- FR-005
