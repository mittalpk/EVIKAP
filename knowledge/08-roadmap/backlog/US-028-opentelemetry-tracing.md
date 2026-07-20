# US-028 — OpenTelemetry Tracing — Basic Observability Setup

## User Story

**As a** Platform Engineer,  
**I want to** instrument the backend and agent services with OpenTelemetry tracing — capturing request spans, per-call LLM token cost, retrieval latency, and the evidence path that produced each answer — exported to a configured observability backend (Langfuse or Arize Phoenix),  
**So that** every query is traceable end-to-end and a synthetic incident (e.g., intentionally broken retrieval) is diagnosable from traces alone without reading raw logs.

---

## Description

This is the PI-1 slice of FEAT-11 (platform hardening) covering NFR-007 (Observability). It instruments the three key spans in the query path: (1) knowledge API retrieval, (2) agent synthesis, (3) guardrails. Each span captures: duration, `trace_id` (shared across the full request), key attributes (query length, top-k, model used, token count, retrieval source count). The `trace_id` is the same identifier returned in the API response and stored in `Query` / `EvidenceItem` / `Answer` records.

---

## Business Value

- Converts "something is slow" from a multi-hour debug exercise into a minutes-long trace-drill.
- Enables the cost-per-query dashboard (NFR-009) — token cost is captured as a span attribute.
- Required for NFR-007 verification: "a synthetic incident is diagnosable from traces alone within a defined MTTD target."

---

## Acceptance Criteria

**Given** the OTel instrumentation is deployed and the observability backend is configured,  
**When** a query is processed end-to-end,  
**Then:**
- A single root span covering the full query lifecycle is created with `trace_id` matching the one returned in the API response.
- Child spans exist for: `knowledge_api.retrieve`, `agent.synthesise`, `guardrails.scan_evidence`, `guardrails.validate_output`.
- Each span includes attributes: `query.length`, `retrieval.top_k`, `retrieval.source_count`, `llm.model`, `llm.input_tokens`, `llm.output_tokens`, `latency_ms`.
- Spans are exported to the configured observability backend (Langfuse or Arize Phoenix; Jaeger for local development).
- NFR-007 done-check: with retrieval intentionally broken (e.g., DB connection refused), the failure span is visible in the trace and identifies the failing component within 5 minutes of the synthetic incident.

---

## Functional Requirements

- Supports FR-008 (Audit log) — `trace_id` links the OTel trace to the `Query` audit record.

---

## Non-Functional Requirements

- NFR-007 (Observability) — this is the primary implementation.
- NFR-009 (Cost optimisation) — `llm.input_tokens` and `llm.output_tokens` per span enable cost tracking.
- NFR-006 (Performance) — OTel instrumentation must add < 5ms to request latency (use async exporters; no synchronous blocking export in the request path).

---

## Dependencies

- US-011 (API query endpoint — the trace root span is created here).
- US-008 (Knowledge API retrieval — child span).
- US-024/US-025 (Guardrails — child spans).
- Observability backend credentials configured in secrets (Langfuse API key, or Jaeger endpoint for local).

---

## Assumptions

- `opentelemetry-sdk` and `opentelemetry-exporter-otlp` (or `opentelemetry-exporter-langfuse`) are added to both `backend/requirements.txt` and `agent/requirements.txt`.
- Local development uses a Jaeger container (added to `docker-compose.yml`).
- Production uses Langfuse (demo profile: Langfuse cloud free tier; enterprise profile: self-hosted Langfuse or Arize Phoenix).
- The `trace_id` is generated as a UUID at the interface tier or agent tier entry point; all downstream services use the same `trace_id` (propagated via HTTP header `X-Trace-ID`).

---

## Edge Cases

- **Observability backend unreachable (Langfuse down):** OTel exporter must be configured with a batch exporter + retry; export failures must not affect query response latency or correctness.
- **High query volume causing OTel export queue backup:** Use a bounded buffer; drop older spans if the buffer fills rather than blocking the request path.
- **Local development without Langfuse credentials:** Fall back to `ConsoleSpanExporter` (logs spans to stdout) if no exporter is configured.

---

## Technical Notes / Implementation Considerations

- **OTel setup:** `opentelemetry-sdk` auto-instrumentation + manual spans for the four key checkpoints.
- **`trace_id` propagation:** Generate at request entry in the agent service; pass to the backend API as `X-Trace-ID` header; backend creates a child span under the same trace.
- **Langfuse integration:** Use `langfuse-python` SDK's OTel exporter, or the standard OTLP exporter pointed at Langfuse's OTLP endpoint.
- **Docker Compose local setup:** Add `jaeger:all-in-one` service; set `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317`.
- **LLM token cost span attribute:** Extract `response.usage_metadata.prompt_token_count` and `response.usage_metadata.candidates_token_count` from the Gemini `GenerateContentResponse`; add as span attributes.
- **Unit tests:** Mock the OTel SDK; assert spans are created with the correct attribute keys (not attribute values — those vary per query).

---

## Definition of Done

- [ ] `opentelemetry-sdk` and exporter added to `backend/requirements.txt` and `agent/requirements.txt`.
- [ ] Root span created per request with `trace_id` matching the API response.
- [ ] Child spans for: `knowledge_api.retrieve`, `agent.synthesise`, `guardrails.scan_evidence`, `guardrails.validate_output`.
- [ ] LLM token count attributes populated.
- [ ] Jaeger service added to `docker-compose.yml` for local development.
- [ ] Langfuse exporter configured for demo/enterprise profiles.
- [ ] NFR-007 done-check: synthetic broken retrieval diagnosable from trace within 5 minutes.
- [ ] OTel export failure does not affect query response.
- [ ] Unit tests: span creation asserted (with mocked OTel SDK).
- [ ] CI passes.

---

## Priority

**Medium** — Required for NFR-007 but does not block pilot go-live (can be introduced in parallel).

## Estimated Effort

**M (Medium)** — ~3–4 days (OTel setup, span instrumentation in 3 services, Jaeger Docker Compose, Langfuse config, tests).

## Related Epics / Features

- FEAT-11 (Platform hardening — observability slice)
- NFR-007 (Observability)
- NFR-009 (Cost optimisation — token cost captured)
