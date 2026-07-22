# Migration and Implementation Roadmap

**TOGAF ADM Phases E & F — Opportunities & Solutions, Migration Planning**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../06-agile-delivery/PI_PLANNING_OBJECTIVES.md](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md) · [../VigilRAG_AUDIT.md](../VigilRAG_AUDIT.md) · [EXECUTION_RUNBOOK.md](EXECUTION_RUNBOOK.md) (task-level detail for Phase 0/1) · [ISSUE_LOG.md](ISSUE_LOG.md) (issues found while executing)

---

## 1. Purpose

Bridges the target architecture (Phases A–D, this knowledge base's `01`–`04` folders) to the current, as-built state documented in the technical audit, and sequences the transition — the TOGAF migration-planning discipline of not designing a target state in a vacuum from where the system actually is today.

## 2. Baseline architecture (as-is)

Per [`VigilRAG_AUDIT.md`](../VigilRAG_AUDIT.md): a three-service split with a genuinely correct trust boundary, keyword/substring retrieval branded as semantic search, a single-pass agent loop branded as iterative multi-agent reasoning, no real database layer, no CI test gate, and infrastructure drift between provisioned network resources and the actually-running Container Apps.

## 3. Gap summary (as-is → target)

| Domain | As-is | Target | Closing feature(s) |
|---|---|---|---|
| Retrieval | Keyword/substring | Hybrid semantic + keyword, reranked, cited | FEAT-02, FEAT-03, FEAT-18 |
| Agent reasoning | Single-pass | Genuinely iterative, bounded | FEAT-04 |
| Data layer | Fictional (filename search) | Real Postgres + vector index, with a defined graduation path to a dedicated vector DB | FEAT-12, FEAT-20, Data Architecture |
| Permissions | No RBAC, single hardcoded admin | Permission-aware retrieval, RBAC | FEAT-06 |
| CI/CD | No test gate | Mandatory evaluation-gated CI | FEAT-11 |
| AI quality assurance | No automated evaluation (manual narrative only) | RAGAS/DeepEval-based evaluation harness gating every retrieval/prompt/model change | FEAT-16 |
| AI safety | No guardrails | Prompt-injection defense + output validation (Guardrails AI/NeMo) + PII redaction (Presidio) | FEAT-17 |
| AI governance | No published transparency artifact | Model/System Card per release, mapped to NIST AI RMF / ISO 42001 | FEAT-19 |
| Observability | stdlib logging only | OpenTelemetry GenAI tracing to Langfuse | FEAT-11 |
| Infrastructure | VNet/NSG provisioned but unused; drifted Terraform state | Reconciled, actually-enforced network isolation | Technology Architecture §6 |
| Agent interface | Internal API only | MCP-standard tool interface | FEAT-10 |
| Relational reasoning | Not present | Knowledge graph (Neo4j) via GraphRAG pattern, layered on vector RAG | FEAT-13 (roadmap, Phase 4+) |

## 4. Migration approach

**Strategy: incremental transformation in place, not a rewrite.** The existing service topology (three tiers, trust-boundary isolation) is architecturally sound and is preserved — see [Application Architecture §8](../04-solution-architecture/APPLICATION_ARCHITECTURE.md#8-deliberately-preserved-from-current-implementation). Migration work targets the gaps in Section 3, not the shape of the system.

**Which deployment profile applies when:** all phases below describe application/architecture maturity, independent of which [deployment profile](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6-deployment-profiles) hosts them. A public demo may run any phase's feature set on the low-cost Netlify/Koyeb/Supabase profile; a real pilot with a sponsoring business unit (Section 5, Phase 1 onward) must run on the enterprise Azure profile, since only that profile is designed to meet the NFR baseline the pilot's acceptance criteria depend on. Do not treat successful demo-profile operation as evidence of NFR conformance — it isn't, by design.

## 5. Sequenced roadmap

### Phase 0 — Discovery & Validation (PI-0)
Corresponds to [Problem/Solution Fit](../05-lean-product/PROBLEM_SOLUTION_FIT.md) validation activities. No production architecture change; a throwaway concierge-style prototype only.

### Phase 1 — Foundation & MVP (PI-1)
- Resolve the highest-severity items independent of new features: rotate any previously exposed credentials, confirm secret-scanning coverage (see [Compliance & Security Framework §4](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md#4-incident-response-posture)).
- Stand up the real data layer (Postgres + pgvector) for code + wiki sources only (MVP scope).
- Implement permission-aware retrieval and pass security review before indexing real content.
- Implement the CI evaluation gate — this is a prerequisite for every subsequent phase, not a nice-to-have. Concretely, this means the RAGAS-based evaluation harness (FEAT-16), not just a build/test check.
- Implement guardrails (FEAT-17: prompt-injection defense + PII redaction) as a precondition for indexing real content, alongside permission enforcement — not a later hardening pass.
- Ship FEAT-01/02/03/06/08(minimal)/09(minimal)/16/17 per [PI-1 objectives](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md#3-pi-1--mvp-trust--adoption-validation).

### Phase 2 — Full Requirement Conformance (PI-2)
- Implement genuine iterative agent reasoning (FEAT-04), replacing the single-pass stub.
- Add the structured/database source connector (FEAT-12).
- Add retrieval reranking (FEAT-18) and Model/System Card publication (FEAT-19), both building on Phase 1's evaluation harness.
- Reconcile Terraform state with actually-running infrastructure (close the VNet/NSG drift) before considering any regulated-data source.
- Complete observability (OpenTelemetry tracing to Langfuse), cost dashboards, and chaos-tested reliability.
- Complete freshness/conflict signaling (FEAT-05) and self-service source registration (FEAT-07).
- Evaluate vector database graduation trigger criteria (FEAT-20, [Technology Architecture §6a](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path)); migrate only if the criteria are actually met, not on a fixed schedule.

### Phase 3 — Platform Expansion (PI-3)
- Ship the MCP-based agent tool interface (FEAT-10), validated against a reference external agent.
- Load-test to enterprise scale; finalize multi-provider model routing/fallback.
- Prepare and present the enterprise-wide rollout business case using pilot-validated (not benchmark) ROI figures.

### Phase 4+ — Enterprise Differentiation (post-epic, contingent on Gate 3 approval)
- Knowledge graph relational retrieval (FEAT-13) — Neo4j populated via entity/relationship extraction, queried through a GraphRAG pattern that routes relationship-shaped questions to the graph and similarity-shaped questions to the existing vector retrieval index; this augments Phase 1–3's RAG stack, it does not replace it.
- Human-in-the-loop approval workflows as a precursor to any future write-back capability (FEAT-14).
- Multi-tenancy, if the platform is validated for delivery across multiple business units or externally (FEAT-15).

## 6. Transition risk

Each phase transition risk is tracked in the [Risk Register](../07-governance-risk/RISK_REGISTER.md); the most migration-specific risk is RISK-008 (infrastructure drift persisting into production) — this roadmap explicitly sequences its resolution into Phase 2, before any regulated-data source can be considered per the [Architecture Governance](../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals) gate.

## 7. Roadmap governance

This roadmap is reviewed and re-baselined at every PI boundary alongside [PI_PLANNING_OBJECTIVES.md](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md); any phase reordering requires Architecture Review Board sign-off per [Architecture Governance §5](../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#5-change-control-for-architecture-decisions).
