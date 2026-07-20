# US-026 — PII Redaction — Microsoft Presidio Integration

## User Story

**As a** Privacy / Compliance Officer,  
**I want to** automatically detect and redact PII (personally identifiable information) from synthesised answers before they are returned to users,  
**So that** the platform never surfaces PII from retrieved source content in its outputs, even when the underlying source documents contain it.

---

## Description

This story integrates Microsoft Presidio for PII detection and redaction in the answer-out guardrail step. PII detected in the synthesised answer is replaced with a placeholder (e.g., `[REDACTED-EMAIL]`, `[REDACTED-PERSON]`) before delivery. The `guardrail_flags` field in the `Answer` record records what PII types were detected. This is distinct from the injection defense (US-024) and output validation (US-025) — PII redaction is a privacy control, not a security control, and must not be conflated with them.

---

## Business Value

- Prevents the platform from becoming a vehicle for inadvertent PII disclosure from source documents.
- Satisfies NFR-003 (Privacy): "PII encountered in retrieved source content shall be identifiable and redactable in synthesised answers."
- Required before the platform can be used with any source content that may contain employee names, email addresses, or other PII.

---

## Acceptance Criteria

**Given** a synthesised answer contains PII (e.g., an email address, a person's name, a phone number),  
**When** the Presidio redaction step runs on the answer text,  
**Then:**
- Detected PII is replaced with a type-specific placeholder: `[REDACTED-EMAIL]`, `[REDACTED-PERSON]`, `[REDACTED-PHONE]`, etc.
- The answer is otherwise unchanged — non-PII content is preserved.
- `guardrail_flags` includes a flag per PII type detected: e.g., `"pii-redacted:EMAIL"`, `"pii-redacted:PERSON"`.
- A PII-tagged test fixture confirms redaction behaviour (NFR-003 verification).
- A function or method name that happens to contain a common first name is not redacted (false positive: Presidio's `PERSON` recogniser must be configured with appropriate context).

---

## Functional Requirements

- FR-012 (Guardrails — PII redaction as part of the answer-out validation step).
- NFR-003 (Privacy — Presidio-based redaction, not ad hoc pattern matching).

---

## Non-Functional Requirements

- NFR-003 (Privacy) — Presidio is a named, auditable PII library; use it rather than ad hoc regex. The choice is documented in the Model/System Card (US-034).

---

## Dependencies

- US-025 (Output validation — the PII redaction step runs within the same answer-out guardrail checkpoint, after schema validation).
- Presidio installed: `presidio-analyzer` and `presidio-anonymizer` added to `backend/requirements.txt` or `agent/requirements.txt`.

---

## Assumptions

- Presidio runs locally (no network call for the analyser); the spaCy `en_core_web_lg` model is used as the NLP engine.
- PII redaction applies to the `answer` text field only; `citations[].content_excerpt` is not redacted (it comes from the source and is already subject to the permission filter).
- False-positive tuning: configure Presidio's `PERSON` recogniser with a deny-list of common programming terms that might be misidentified (e.g., `Alice`, `Bob` in code examples). Extend the deny-list as false positives are discovered.
- The spaCy model download is included in the Docker image build; not downloaded at runtime.

---

## Edge Cases

- **Answer is entirely PII:** Return the answer with all PII replaced by placeholders; do not reject it. Add `guardrail_flags: ["pii-redacted:ALL"]`.
- **Presidio model not loaded (startup failure):** Fail-closed: refuse to return the answer; return HTTP 503.
- **PII in a code block within the answer (e.g., an email address in a code example):** PI-1: redact it. A more nuanced code-block exclusion (parallel to the injection defense's code fence exclusion) is a PI-2 refinement.
- **Non-English content in the answer:** Presidio's multilingual support is limited; log a warning if the detected language is not English; do not suppress the redaction attempt.

---

## Technical Notes / Implementation Considerations

- **Implementation:** Add a `pii_redact(text: str) -> RedactionResult` function to `agent/app/guardrails.py`.
- **`RedactionResult`:** `{redacted_text: str, detected_entities: list[{entity_type, start, end}]}`.
- **Presidio setup:** `AnalyzerEngine` with `SpacyNlpEngine` (`en_core_web_lg`); `AnonymizerEngine` with `Replace` operator using type-specific placeholders.
- **Placement in the answer-out checkpoint:** After schema validation (US-025), before returning the `QueryResponse`; replace `response["answer"]` with `redacted_text` and extend `guardrail_flags` with detected entity types.
- **spaCy model in Docker:** Add `RUN python -m spacy download en_core_web_lg` to `agent/Dockerfile`.
- **Unit tests:** A fixture answer with a known email address is redacted; a code identifier `AliceBlue` (CSS colour) is not flagged as a person name; `guardrail_flags` contains the correct entity types.

---

## Definition of Done

- [ ] `presidio-analyzer` and `presidio-anonymizer` added to `agent/requirements.txt`.
- [ ] `pii_redact()` function implemented in `agent/app/guardrails.py`.
- [ ] spaCy `en_core_web_lg` model downloaded in `agent/Dockerfile`.
- [ ] PII replaced with type-specific placeholders in the answer.
- [ ] `guardrail_flags` updated with detected PII types.
- [ ] Presidio startup failure → HTTP 503 (fail-closed).
- [ ] Unit tests: email redacted, person name redacted, code identifier not falsely flagged.
- [ ] NFR-003 PII-tagged fixture test passes.
- [ ] CI passes.
- [ ] Execution Runbook §4.5 third bullet marked `[x]`.

---

## Priority

**High** — Required before indexing any source content that may contain PII.

## Estimated Effort

**M (Medium)** — ~2–3 days (Presidio setup, Docker model download, redaction integration, false-positive tuning, tests).

## Related Epics / Features

- FEAT-17 (Guardrails: PII redaction)
- NFR-003 (Privacy)
- Execution Runbook §4.5
