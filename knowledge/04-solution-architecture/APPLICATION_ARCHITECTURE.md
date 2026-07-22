# Application Architecture

**TOGAF ADM Phase C — Information Systems Architecture (Application)**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) · [TECHNOLOGY_ARCHITECTURE.md](TECHNOLOGY_ARCHITECTURE.md) · [../VigilRAG_AUDIT.md](../VigilRAG_AUDIT.md)

---

## 1. Purpose

Defines the target service decomposition, responsibilities, and interaction contracts. This builds forward from the existing three-service split validated in the current codebase, correcting the gaps the audit identified rather than discarding what already works.

## 2. Service decomposition (target state)

| Service | Responsibility | Carries source credentials? | Status relative to current build |
|---|---|---|---|
| **Interface tier** | Human UI (web) + chat-platform integrations | No | Exists (React SPA); needs test coverage, componentization |
| **Knowledge API (retrieval tier)** | Source connectors, indexing pipeline, permission enforcement, hybrid semantic+keyword retrieval, source registry | **Yes — only service that does** | Exists as a keyword-only implementation; requires the RAG upgrade specified in [Data Architecture](DATA_ARCHITECTURE.md) |
| **Agent orchestration tier** | Query decomposition, iterative evidence-gathering, answer synthesis, citation assembly | No | Exists as a single-pass LangGraph skeleton; requires genuine iteration per FR-004 |
| **Evaluation service** | Runs golden-dataset RAGAS/DeepEval evaluation (NFR-011) on every retrieval/prompt/model change; gates CI; records `EvaluationRun` results that Model/System Cards must match | No | Does not exist today — net-new |
| **Guardrails service** | Scans retrieved content for prompt-injection patterns before it reaches the synthesis model; validates synthesized output against a structural/safety schema before it leaves the orchestration tier (FR-012) | No | Does not exist today — net-new |
| **Reranking step** (library call inside the retrieval tier, not a separate service) | Re-orders hybrid-retrieval candidates by a cross-encoder/rerank model before evidence is returned to the orchestration tier (FR-011) | No | Does not exist today — net-new |
| **Audit & observability service** | Ingests traces, cost/latency metrics, and the provenance log; serves compliance queries | No (read access to logs only) | Does not exist today — net-new |
| **Agent tool gateway (MCP)** | Exposes the Knowledge API's query capability as a standards-based tool for external/internal AI agents | No | Does not exist today — net-new; wraps the existing internal API |
| **Model/System Card publisher** | Generates and publishes a Card per deployed pipeline version, sourced from the Evaluation service's `EvaluationRun` record (FR-013) | No | Does not exist today — net-new; a lightweight CI-triggered step, not a running service |

## 3. Preserved architectural decision: the trust boundary

The single most important application-architecture decision already made correctly in the existing build is preserved unchanged: **the agent orchestration tier has no source-system SDK access and can reach data only through the Knowledge API.** This is enforced at the network layer (no external ingress to the orchestration tier) and at the code layer (no source-system client libraries imported there). Every new service added in this target architecture (evaluation, audit, MCP gateway) must observe the same rule — none of them may bypass the Knowledge API to reach source systems directly.

## 4. Service interaction contract (primary flow)

```
Interface tier / MCP gateway
        | POST /v1/query {text, requester_identity}
        v
Agent orchestration tier
        | plan -> decompose into sub-queries
        | execute -> call Knowledge API per sub-query (parallel where independent)
        v
Knowledge API (retrieval tier)
        | enforce permission (requester_identity vs source ACL)
        | hybrid retrieval (semantic + keyword) against retrieval index
        | rerank candidates (FR-011) before returning
        | return ranked, cited evidence
        v
Guardrails service: scan retrieved evidence for prompt-injection patterns (FR-012)
        v
Agent orchestration tier
        | evaluate -> is evidence sufficient? if not, re-plan (bounded by max_iterations)
        | synthesize -> compose answer with citations
        v
Guardrails service: validate synthesized output before it leaves the tier (FR-012)
        v
Audit & observability service (async, logged regardless of caller)
        v
Response returned to caller with citations + freshness/conflict flags + any guardrail_flags
```

## 5. API contract principles

- **Versioned from day one** (`/api/v1/...`) — already a positive pattern in the existing build, to be preserved and formalized with an explicit deprecation policy.
- **Machine and human consumers share the same underlying query contract**; the MCP gateway is a protocol adapter over the same `/v1/query` capability, not a parallel implementation.
- **Every response is a typed object** with `answer`, `citations[]`, `confidence/freshness signal`, and `trace_id` — never free text alone, so downstream agents can programmatically use citations rather than re-parsing prose.

## 6. Cross-cutting application concerns

| Concern | Application-architecture requirement |
|---|---|
| Authentication | Every service-to-service call authenticated (existing internal-key pattern, hardened with constant-time comparison everywhere — closes an inconsistency the audit found in the auth router) |
| Authorization | RBAC enforced at the Knowledge API and Interface tier — replacing the current single-hardcoded-admin model |
| Rate limiting | Applied at the Interface tier and MCP gateway to protect the Knowledge API from abusive query volume |
| Caching | Retrieval-result caching moves from the current unbounded per-process dict to a shared, bounded, evicting distributed cache (see [Technology Architecture](TECHNOLOGY_ARCHITECTURE.md)) so it is effective under horizontal scale-out and doesn't leak memory |
| Model routing | Encapsulated inside the orchestration tier as a routing policy (planning model vs. synthesis model), not hardcoded per call site |
| Evaluation gating | The evaluation service is a required CI dependency for the orchestration and retrieval tiers — no deploy without a passing evaluation run |
| Guardrail enforcement | The guardrails service runs at two checkpoints (evidence-in, answer-out per the flow above) and is not optional or bypassable per-call — a request that fails guardrail validation is rejected, not silently degraded |

## 7. Mapping to functional requirements

| Service | Functional requirements realized |
|---|---|
| Interface tier | FR-001 |
| Knowledge API (incl. reranking) | FR-002, FR-005, FR-006, FR-007, FR-011 |
| Agent orchestration tier | FR-001, FR-003, FR-004 |
| Guardrails service | FR-012 |
| Evaluation service | Supports FR-003, FR-009 acceptance verification; NFR-011 |
| Model/System Card publisher | FR-013 |
| Audit & observability service | FR-008 |
| MCP gateway | FR-010 |

## 8. Deliberately preserved from current implementation

- Three-tier service split with the trust boundary as its organizing principle.
- API versioning convention.
- Health-probe pattern (already correctly wired to container orchestration in the current build).

## 9. Deliberately changed from current implementation

- Retrieval logic moves from keyword/substring matching to hybrid semantic retrieval (see [Data Architecture §4](DATA_ARCHITECTURE.md#4-conceptual-data-flow)).
- Agent orchestration's `evaluate`/`should_continue` logic becomes real, bounded iteration (FR-004) instead of a no-op.
- Two net-new services (evaluation, audit/observability) are added as first-class citizens, not bolted on later.
