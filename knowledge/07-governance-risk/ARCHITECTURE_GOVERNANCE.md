# Architecture Governance

**TOGAF ADM Phase G — Implementation Governance**
**Status:** Draft · **Version:** 1.0 · 2026-07-14

---

## 1. Purpose

Defines who has authority to approve architecture decisions and changes for VigilRAG, and how ongoing compliance with the baselined architecture (this knowledge base) is checked.

## 2. Governance body

**Architecture Review Board (ARB)** — convened per TOGAF phase gate and for any architecture-significant change thereafter.

| Role | Represents |
|---|---|
| AI Solutions Architect (chair) | Overall architecture coherence, TOGAF process |
| Security engineering delegate | Trust-boundary and permission-model integrity |
| Platform engineering lead | Technology architecture feasibility and operability |
| Compliance/data governance delegate | Regulatory and audit requirements |
| Product owner | Business architecture and requirements alignment |

## 3. Phase-gate approvals

| Gate | Reviews | Approves progression to |
|---|---|---|
| Architecture Vision review | [01-architecture-vision](../01-architecture-vision/ARCHITECTURE_VISION.md) | Business Architecture work |
| Business Architecture review | [02-business-architecture](../02-business-architecture) | Business analysis / requirements elicitation |
| Requirements baseline review | [03-business-analysis](../03-business-analysis) | Solution architecture design |
| Solution architecture review | [04-solution-architecture](../04-solution-architecture) | MVP build (subject to Lean Product/Epic Hypothesis funding gates running in parallel) |
| Pre-production security review | Permission model, trust boundary, secrets handling, guardrails (FEAT-17) | Any go-live against real (even low-sensitivity) source content |
| Regulated-data onboarding review | Data classification, redaction, audit controls | Onboarding any source containing PII/PHI/financial data |
| Production release gate | Model/System Card (FR-013) is current and its scores match the evaluation harness's `EvaluationRun` record for that exact version | Any production deploy, from PI-2 onward once FEAT-19 exists |

## 4. Architecture compliance checking

Every feature in the [Program Backlog](../06-agile-delivery/PROGRAM_BACKLOG.md) is checked against these non-negotiable architecture principles (from [Architecture Vision §7](../01-architecture-vision/ARCHITECTURE_VISION.md#7-architecture-principles)) before being marked done:

1. No reasoning component holds source-system credentials.
2. No answer is synthesized without retrieved grounding evidence.
3. No retrieval/prompt/model change reaches production without passing the automated evaluation gate (RAGAS/DeepEval, NFR-011).
4. No retrieval result exposes content beyond the requester's source-system permissions.
5. Every request is traceable end-to-end, including cost.
6. No retrieved content reaches the synthesis model without passing guardrail prompt-injection screening, and no synthesized output is delivered without passing guardrail output validation (FR-012).
7. No production pipeline version ships without a current Model/System Card whose published scores match the evaluation harness's own record for that version (FR-013, NFR-012).

A feature that violates any of these is **not compliant regardless of functional correctness** and is blocked from production release until remediated — this is the same discipline that caught and remediated the fabricated-database-fallback issue documented in the current-state [audit](../VigilRAG_AUDIT.md), applied prospectively rather than retrospectively.

## 5. Change control for architecture decisions

| Change type | Approval required |
|---|---|
| Addition of a new source connector type | ARB review (security + platform delegates minimum) |
| Change to the trust-boundary model | Full ARB, plus budget owner sign-off (treated as an epic-level risk event) |
| Technology substitution (e.g., swapping vector store product) | Platform engineering lead + AI Solutions Architect, logged in [Technology Architecture](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md) changelog |
| New NFR target | ARB review, traced through [Requirements Management Plan](../03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md) change process |

## 6. Architecture debt tracking

Any deliberate short-term deviation from the target architecture (e.g., MVP's single-pass synthesis before FEAT-04 lands) is logged here as **accepted architecture debt** with an explicit repayment PI, not left undocumented:

| Debt item | Accepted in | Repayment target |
|---|---|---|
| Single-pass synthesis (FEAT-04 iteration deferred) | PI-1 (MVP) | PI-2 |
| Database/structured source connector absent | PI-1 (MVP) | PI-2 (FEAT-12) |
| Full compliance-grade audit log (minimal version only) | PI-1 (MVP) | PI-2 |
| MCP agent interface absent | PI-1/PI-2 | PI-3 (FEAT-10) |
| Retrieval reranking absent (initial hybrid retrieval score only) | PI-1 (MVP) | PI-2 (FEAT-18) |
| Model/System Card publication absent | PI-1 (MVP) | PI-2 (FEAT-19) |
| Knowledge graph / GraphRAG absent | PI-1 through PI-3 | Post-PI-3 (FEAT-13) — not accepted as debt against MVP scope, since relational retrieval was never claimed at MVP; listed here only for completeness |

## 7. Relationship to SAFe governance

Architecture governance operates in parallel with, not instead of, SAFe PI-level business governance ([PI_PLANNING_OBJECTIVES.md](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md)) and Lean funding gates ([EPIC_HYPOTHESIS.md](../06-agile-delivery/EPIC_HYPOTHESIS.md)). A feature can be business-approved for a PI and still be blocked from release by an unresolved architecture compliance finding — the two governance tracks are independent checks, by design.
