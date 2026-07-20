# US-025 — Output Validation — Structural / Safety Schema Check

## User Story

**As a** Security Engineer,  
**I want to** validate every synthesised answer against a structural and safety schema before it is returned to the caller, and reject any response that fails validation,  
**So that** malformed, harmful, or schema-invalid outputs are never delivered to end users or downstream agents.

---

## Description

This is the "answer-out" guardrail checkpoint described in FR-012 and the [Application Architecture §4](../../04-solution-architecture/APPLICATION_ARCHITECTURE.md#4-service-interaction-contract-primary-flow). After the LLM synthesises an answer, the Guardrails service validates the output against: a schema check (answer is a non-empty string, citations is a list, etc.) and a safety check (answer does not contain explicit harmful content, does not appear to execute an injected instruction). Responses that fail are rejected — not silently degraded — and the caller receives an HTTP 503 with an appropriate error.

---

## Business Value

- Ensures EVIKAP never delivers malformed or harmful output, protecting user trust and the platform's reputation.
- Satisfies FR-012's "answer-out" acceptance check: "a fixture producing a malformed or unsafe output is rejected before delivery."

---

## Acceptance Criteria

**Given** the synthesis model has produced an answer,  
**When** the output validation step runs,  
**Then:**
- A schema validation check confirms: `answer` is a non-empty string; `citations` is a list (may be empty); `trace_id` is present.
- A safety check confirms the answer does not: begin with or contain the injected instruction text from the fixture suite; contain explicit harmful content (hate speech, self-harm instructions, etc.) as detected by the safety classifier.
- A response that fails schema validation is rejected with HTTP 503; a structured error is returned: `{"error": "output-validation-failed", "reason": "schema-invalid"}`.
- A response that fails the safety check is rejected with HTTP 503; `{"error": "output-validation-failed", "reason": "safety-check-failed"}`.
- Rejected responses are logged with `trace_id`, the failure reason, and the first 200 characters of the rejected output (for debugging).
- `guardrail_flags` in the `Answer` record includes the rejection reason.

---

## Functional Requirements

- FR-012 (Guardrails: output validation — answer-out checkpoint).

---

## Non-Functional Requirements

- NFR-002 (Security) — the validation step is not optional or bypassable; it runs on every synthesis output.
- NFR-007 (Observability) — rejected outputs are logged with full context for debugging.

---

## Dependencies

- US-024 (Prompt-injection defense — both checkpoints live in the same `GuardrailsClient`).
- US-011 (API query endpoint — the answer-out checkpoint inserts after synthesis and before response).
- US-027 (Guardrails CI test suite — fixtures for unsafe output used in tests).

---

## Assumptions

- For the safety check, PI-1 uses a rule-based safety classifier (banned phrase list + Gemini safety filters) rather than a full moderation model. A dedicated moderation model (e.g., Perspective API) is a PI-2 hardening.
- Schema validation uses a Pydantic model — `QueryResponse` already defined in US-011; the output validation step instantiates a `QueryResponse` from the raw LLM output and catches `ValidationError`.
- If the safety classifier is a network call (e.g., Gemini safety filter), failure of that call is treated as fail-closed (output rejected, not passed through).

---

## Edge Cases

- **LLM output is valid JSON but fails the Pydantic schema (missing field):** Reject; log the schema error with the specific missing field.
- **LLM safety filter rate-limited:** Fail-closed; return HTTP 503. Do not bypass the safety check.
- **LLM answer is a single word "Sorry" (uninformative but structurally valid):** Pass the schema check; do not reject a valid-but-uninformative answer. This is a retrieval quality issue, not a safety issue.
- **Rejected output is logged but the log itself contains harmful content:** Truncate log to 200 characters; do not emit the full harmful output to the log stream.

---

## Technical Notes / Implementation Considerations

- **Implementation:** Extend `agent/app/guardrails.py`'s `GuardrailsClient` with a `validate_output(response: dict) -> ValidationResult` method.
- **Schema validation:** `QueryResponse.model_validate(response)` — Pydantic raises `ValidationError` on schema failures.
- **Safety check (PI-1):** Check that `response["answer"]` does not start with any of the injection fixture patterns (simple prefix match); check Gemini's response safety ratings (available in the `GenerateContentResponse` object's `safety_ratings` field — if any rating is `BLOCK_REASON_*`, treat as failed).
- **Logging:** `logger.error("output_validation_failed", trace_id=..., reason=..., output_excerpt=response["answer"][:200])`.
- **Answer-out checkpoint placement in US-011:** Between synthesis and the return statement; wraps the `QueryResponse` assembly step.

---

## Definition of Done

- [ ] `GuardrailsClient.validate_output()` implemented with schema and safety checks.
- [ ] Schema failure → HTTP 503 with `"reason": "schema-invalid"`.
- [ ] Safety failure → HTTP 503 with `"reason": "safety-check-failed"`.
- [ ] Rejected outputs logged with `trace_id`, reason, and truncated output excerpt.
- [ ] `guardrail_flags` updated in `Answer` record for rejected outputs.
- [ ] Unit tests: valid output passes; schema-invalid output rejected; safety-failing fixture output rejected.
- [ ] US-027 safety fixture suite passes.
- [ ] CI passes.
- [ ] Execution Runbook §4.5 second bullet marked `[x]`.

---

## Priority

**High** — Required before any real content is indexed.

## Estimated Effort

**S (Small)** — ~1–2 days (extends US-024's `GuardrailsClient`; schema check is a Pydantic call; safety check is a filter on Gemini's response).

## Related Epics / Features

- FEAT-17 (Guardrails: output validation)
- FR-012 (Guardrails)
- Execution Runbook §4.5
