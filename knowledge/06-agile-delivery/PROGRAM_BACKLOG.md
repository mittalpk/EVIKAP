# Program Backlog

**SAFe — Program Backlog (Features realizing EPIC-01)**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [EPIC_HYPOTHESIS.md](EPIC_HYPOTHESIS.md) · [../03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md](../03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md)

---

## 1. Purpose

Decomposes EPIC-01 into features, each traced to functional/non-functional requirements, prioritized by MoSCoW at this level and sequenced into the PIs defined in [PI_PLANNING_OBJECTIVES.md](PI_PLANNING_OBJECTIVES.md).

## 2. Feature list

| ID | Feature | Realizes | MoSCoW | Target PI |
|---|---|---|---|---|
| FEAT-01 | Unified query interface (UI) | FR-001 | Must | PI-1 (MVP) |
| FEAT-02 | Hybrid semantic + keyword retrieval (code + wiki sources) | FR-002 | Must | PI-1 (MVP) |
| FEAT-03 | Provenance and citation rendering | FR-003 | Must | PI-1 (MVP) |
| FEAT-04 | Iterative multi-agent reasoning loop (real evaluate/re-plan) | FR-004 | Must | PI-2 |
| FEAT-05 | Freshness and conflict signaling | FR-005 | Should | PI-2 |
| FEAT-06 | Permission-aware retrieval enforcement | FR-006 | Must | PI-1 (MVP) |
| FEAT-07 | Source registration self-service workflow | FR-007 | Should | PI-2 |
| FEAT-08 | Audit and access-review log | FR-008 | Must | PI-1 (MVP, minimal) / PI-2 (full compliance-grade) |
| FEAT-09 | Feedback and correction loop into evaluation dataset | FR-009 | Must | PI-1 (MVP, minimal) |
| FEAT-10 | MCP-based agent tool interface | FR-010 | Should | PI-3 |
| FEAT-11 | Platform hardening (all NFR-001 through NFR-010) | NFR-001…010 | Must | Spans PI-1 through PI-3, weighted toward PI-1 for security/observability basics |
| FEAT-12 | Structured/database source connector | (extends FR-002 scope) | Should | PI-2 |
| FEAT-13 | Knowledge graph relational retrieval (Neo4j, GraphRAG pattern layered on vector RAG, not a replacement for it) | Roadmap (post Problem Statement §10.3) | Could | Post-PI-3 |
| FEAT-14 | Human-in-the-loop approval workflow (precursor to any future write-back) | Roadmap | Could | Post-PI-3 |
| FEAT-15 | Multi-tenancy | Roadmap | Won't (this program) | Future program increment beyond this epic's current funding gate |
| FEAT-16 | RAG evaluation harness (RAGAS primary, DeepEval fallback) against a versioned golden dataset, CI-gated | NFR-011 | Must | PI-1 (MVP) |
| FEAT-17 | Guardrails: prompt-injection defense (Guardrails AI / NeMo Guardrails) + PII redaction (Presidio) | FR-012 | Must | PI-1 (MVP) |
| FEAT-18 | Retrieval reranking (cross-encoder or Cohere Rerank) after hybrid retrieval | FR-011 | Should | PI-2 |
| FEAT-19 | Model/System Card publication per deployed pipeline version | FR-013, NFR-012 | Should | PI-2 |
| FEAT-20 | Vector database graduation (pgvector → Qdrant/Weaviate) | Technology Architecture §6a | Could | Trigger-based — see §5a, not tied to a fixed PI |

## 3. Feature detail — MVP-critical (PI-1)

### FEAT-01 Unified query interface
**Enabler type:** Business feature. **Acceptance:** per FR-001. **Dependencies:** none (can start immediately).

### FEAT-02 Hybrid semantic + keyword retrieval
**Enabler type:** Architectural enabler + business feature. **Acceptance:** per FR-002, scoped to code + wiki sources only for MVP per [MVP Definition §3](../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp). **Dependencies:** Data Architecture retrieval index (vector store provisioning).

### FEAT-03 Provenance and citation
**Enabler type:** Business feature. **Acceptance:** per FR-003. **Dependencies:** FEAT-02 (citations require retrieval evidence to point to).

### FEAT-06 Permission-aware retrieval
**Enabler type:** Architectural enabler (security-critical). **Acceptance:** per FR-006, verified via the permission-matrix test suite. **Dependencies:** identity provider integration; must pass security architecture review (per [Problem/Solution Fit §3](../05-lean-product/PROBLEM_SOLUTION_FIT.md#3-solution-validation-does-this-specific-solution-fit-the-validated-problem)) before FEAT-02 can go live against real content.

### FEAT-08 Audit log (minimal, PI-1 scope)
**Enabler type:** Architectural enabler. **Acceptance:** query + evidence + requester identity logged; full compliance-grade retention/review tooling deferred to PI-2.

### FEAT-11 Platform hardening (PI-1 slice)
**PI-1 scope:** CI test gate (NFR-010), basic observability tracing (NFR-007 minimal), constant-time auth comparisons and RBAC foundation (NFR-002). Full cost-optimization dashboards and chaos-tested reliability (NFR-005, NFR-009) deferred to PI-2.

### FEAT-16 RAG evaluation harness
**Enabler type:** Architectural enabler (quality-critical). **Acceptance:** per NFR-011 — CI blocks merge on a defined regression threshold against a versioned golden dataset; a production quality-trend dashboard is live. **Dependencies:** FEAT-02 (needs real retrieval to evaluate); elevated to Must/PI-1 per [MVP Definition §3](../05-lean-product/MVP_DEFINITION.md#3-in-scope-for-mvp) revision — this is not deferred to PI-2 because ungated retrieval changes against real MVP content are an unacceptable risk, not a scope-reduction opportunity.

### FEAT-17 Guardrails
**Enabler type:** Architectural enabler (security-critical). **Acceptance:** per FR-012 — a maintained prompt-injection test suite is blocked/neutralized; malformed/unsafe outputs are rejected before delivery. **Dependencies:** FEAT-06 (permission enforcement) and FEAT-02; sequenced as a precondition for indexing real content, the same way FEAT-06 already is.

## 4. Feature detail — Fast-follow (PI-2)

FEAT-04 (real iterative reasoning), FEAT-05 (freshness/conflict), FEAT-07 (self-service source onboarding), FEAT-12 (database connector), FEAT-18 (reranking — extends FEAT-02 once corpus size makes it worthwhile per [MVP Definition §4](../05-lean-product/MVP_DEFINITION.md#4-explicitly-deferred-past-mvp)), FEAT-19 (Model/System Cards — depends on FEAT-16's `EvaluationRun` history existing), and the remainder of FEAT-11 hardening. This PI is what converts the MVP from "trust/adoption validated" into a system meeting the full [Functional](../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) and [Non-Functional](../03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) requirement sets.

## 5. Feature detail — Platform expansion (PI-3)

FEAT-10 (MCP interface) — deliberately sequenced after human-adoption validation (per [MVP Definition §4](../05-lean-product/MVP_DEFINITION.md#4-explicitly-deferred-past-mvp)) so machine-consumer validation is not confounded with human-consumer validation.

## 5a. Trigger-based feature: FEAT-20 vector database graduation

Unlike every other feature in this backlog, FEAT-20 is not assigned to a fixed PI — it is triggered by the criteria in [Technology Architecture §6a](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path) (corpus size, latency, filtering complexity, operational load). When two or more trigger signals are met, open a PI-level spike regardless of which PI is currently in flight, rather than waiting for a "natural" slot in the sequence above — this is a deliberate exception to normal backlog sequencing because the cost of migrating too late (production degradation) exceeds the cost of a mid-PI spike.

## 6. Backlog governance

This backlog is refined weekly by the delivery team (per [Business Analysis Plan §3](../03-business-analysis/BUSINESS_ANALYSIS_PLAN.md#3-stakeholder-engagement-plan)) and re-prioritized at each PI boundary using WSJF at the story level, MoSCoW at the feature level shown above. Any feature promoted from "Could"/"Won't" to "Must" requires a change per [Requirements Management Plan §3](../03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md#3-requirements-approval-and-change-process).
