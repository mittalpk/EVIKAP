# US-024 — Prompt-Injection Defense — Retrieved Content Scan

## User Story

**As a** Security Engineer,  
**I want to** scan all retrieved chunks for prompt-injection patterns before they are passed to the synthesis model, and neutralise any detected injection attempts,  
**So that** malicious content embedded in source documents cannot hijack the LLM's behaviour or cause it to produce unintended outputs.

---

## Description

Prompt injection is an attack where malicious instructions embedded in retrieved content are treated by the LLM as instructions from the system or user. This story implements the "evidence-in" guardrail checkpoint: retrieved chunks are scanned before they are added to the synthesis prompt, and any chunk containing injection patterns is either stripped of the injection or excluded from the context. This is a hard prerequisite for indexing real source content per [Execution Runbook §4.5](../EXECUTION_RUNBOOK.md#45-guardrails-feat-17-fr-012).

---

## Business Value

- Prevents a critical AI safety risk from materialising in the live system.
- Satisfies the FR-012 "evidence-in" acceptance check: injection patterns in fixture source documents are blocked/neutralised.
- Required before indexing any real content (same gate as permission enforcement).

---

## Acceptance Criteria

**Given** the agent orchestration tier has retrieved evidence chunks and is preparing to call the synthesis model,  
**When** the Guardrails service scans the retrieved content,  
**Then:**
- Any chunk containing a known prompt-injection pattern (from the maintained fixture suite in US-027) is flagged.
- Flagged chunks are either: sanitised (injection instruction removed, surrounding content preserved) or excluded from the synthesis context entirely (configurable per pattern severity).
- The original chunk content is never modified in the database — only the copy passed to the synthesis prompt is sanitised.
- A `guardrail_flags` entry is added to the `Answer` record for any query where an injection was detected: e.g., `"injection-detected-in-chunk-<chunk_id>"`.
- The synthesised answer is not affected by the injected instruction — the injected instruction has no observable effect on the output.
- No false positive: a legitimate code comment containing `"ignore previous instructions"` within a clearly code-formatted block (triple backtick fenced) is not flagged as an injection.

---

## Functional Requirements

- FR-012 (Guardrails: prompt-injection defense — evidence-in checkpoint).

---

## Non-Functional Requirements

- NFR-002 (Security) — the guardrail is not bypassable per-call; it is applied to every retrieved chunk before synthesis regardless of caller.
- NFR-007 (Observability) — injection detection events are logged with `trace_id`, `chunk_id`, and the detected pattern.

---

## Dependencies

- US-011 (API query endpoint — the evidence-in checkpoint inserts between the retrieval call and the synthesis step in the agent tier).
- US-027 (Guardrails CI test suite — fixture injection patterns used to validate this implementation).

---

## Assumptions

- For PI-1, the guardrails implementation uses Guardrails AI (`guardrails-ai` package) with a custom injection validator, or NVIDIA NeMo Guardrails if preferred by the team.
- The "false positive" heuristic: content within triple-backtick code fences (```` ``` ````) is treated as code and not scanned for injection patterns (since legitimate code often contains instruction-like language).
- Pattern severity levels: `high` → exclude chunk entirely; `medium` → sanitise (remove the injected instruction phrase); `low` → log only.

---

## Edge Cases

- **All retrieved chunks are flagged:** Return an empty evidence list to synthesis; generate an answer of "I could not find reliable information — all retrieved content was flagged by safety guardrails." Add `guardrail_flags: ["all-evidence-flagged"]`.
- **Injection pattern spans multiple chunks:** Each chunk is evaluated independently; partial injection (split across chunks) may not be detected by single-chunk scanning — log this as a known limitation.
- **Guardrails service unavailable:** Fail-closed: block the synthesis call; return HTTP 503. Do not proceed without guardrail validation.
- **New injection pattern discovered:** Add to the fixture suite (US-027) and update the pattern list — no code change required if pattern config is external YAML.

---

## Technical Notes / Implementation Considerations

- **Implementation location:** `agent/app/guardrails.py` — a `GuardrailsClient` class with an `scan_evidence(chunks: list[EvidenceItem]) -> GuardrailsResult` method.
- **GuardrailsResult:** `{safe_chunks: list[EvidenceItem], flagged_chunks: list[FlaggedChunk], injection_events: list[InjectionEvent]}`.
- **Pattern list:** Stored in `agent/app/guardrails_patterns.yaml`; loaded at startup. Patterns include: `"ignore previous instructions"`, `"disregard system prompt"`, `"you are now"`, `"pretend to be"`, etc. — plus the maintained fixture patterns from US-027.
- **Code fence exclusion:** Strip content between triple backticks before scanning; scan the remaining text.
- **Logging:** `logger.warning("injection_detected", trace_id=..., chunk_id=..., pattern=..., severity=...)`.
- **Stub for earlier stories:** US-011 used a `PassthroughGuardrailsClient`; replace it with this real implementation.

---

## Definition of Done

- [ ] `agent/app/guardrails.py` `GuardrailsClient.scan_evidence()` implemented.
- [ ] `agent/app/guardrails_patterns.yaml` with initial pattern list (minimum 10 patterns).
- [ ] Code fence exclusion implemented and tested.
- [ ] `guardrail_flags` written to `Answer` records for detected injections.
- [ ] All injection events logged with `trace_id`, `chunk_id`, and pattern.
- [ ] Fail-closed: guardrail service unavailable → HTTP 503.
- [ ] Unit tests: known injection pattern flagged; code-fenced injection not flagged; all-chunks-flagged case.
- [ ] US-027 fixture suite passes (done-check from US-027's perspective, but the fixture suite must be available for this story's tests).
- [ ] CI passes.
- [ ] Execution Runbook §4.5 first bullet marked `[x]`.

---

## Priority

**High** — Hard prerequisite for indexing real content.

## Estimated Effort

**M (Medium)** — ~3–4 days (GuardrailsClient, pattern YAML, code fence heuristic, logging, unit tests).

## Related Epics / Features

- FEAT-17 (Guardrails: prompt-injection defense + PII redaction)
- FR-012 (Guardrails)
- Execution Runbook §4.5
