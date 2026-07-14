# MVP Definition

**Lean Product Development — Minimum Viable Product Scope**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [PROBLEM_SOLUTION_FIT.md](PROBLEM_SOLUTION_FIT.md) · [../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md)

---

## 1. Purpose

Defines the smallest slice of Omega Nexus that tests the riskiest remaining assumption (from [Problem/Solution Fit §5](PROBLEM_SOLUTION_FIT.md#5-what-fit-looks-like-exit-criteria-for-this-phase)) with real users and real production-adjacent conditions — deliberately smaller than the full functional requirements set.

## 2. MVP hypothesis

> If we give a defined pilot group real, cited, semantically-retrieved answers across their two highest-value knowledge sources (code + wiki), median time-to-answer for in-scope question types will drop measurably within the pilot window, and users will voluntarily choose Omega Nexus over their current search habit at least half the time.

## 3. In scope for MVP

| Capability | Included? | Rationale |
|---|---|---|
| Unified query interface (UI only, no MCP yet) | Yes | Needed to test human trust/adoption — the primary MVP hypothesis |
| Semantic retrieval — code + wiki sources only | Yes | The two source types validated as highest-value in problem validation; database source deferred |
| Provenance/citations | Yes | Non-negotiable — trust cannot be tested without it |
| Single-pass agent synthesis (not yet fully iterative) | Yes, minimal | Iteration (FR-004) adds engineering cost without being the riskiest assumption under test in MVP; a defensible, explicitly-scoped-down starting point |
| Permission-aware retrieval | Yes | Non-negotiable — cannot pilot against real content without it, per security review gate |
| Basic audit log | Yes, minimal | Required before touching any real (even if low-sensitivity) source content |
| Feedback capture (thumbs up/down) | Yes | Cheapest possible signal for the evaluation dataset bootstrap |
| Automated RAG evaluation (RAGAS-based, FR-011/NFR-011) | Yes | **Elevated from "manual sign-off" to "automated, in MVP"** — see revised §4 rationale below. Without this, MVP-stage retrieval changes have no regression signal, which undermines the trust hypothesis the MVP exists to test |
| Guardrails: prompt-injection defense + output validation (FR-012) | Yes, minimal | Real source content is indexed and queried in MVP (per permission-aware retrieval above); guardrails are a precondition for that, not a later hardening pass, the same way permission enforcement already is |

## 4. Explicitly deferred past MVP

| Capability | Deferred to | Rationale |
|---|---|---|
| Database/structured-data source | Fast-follow PI | Problem validation targets code+wiki as highest value first; database connector adds permission-model complexity better tackled once the pattern is proven |
| Full iterative multi-hop reasoning (FR-004 in full) | Fast-follow PI | Single-pass synthesis is sufficient to test the trust/adoption hypothesis; iteration is an answer-quality lever to add once baseline trust is established |
| MCP/agent tool interface (FR-010) | Post-pilot | Machine-consumer validation is a distinct hypothesis from human-adoption validation; sequencing them together would confound what's actually being learned |
| Freshness/conflict signaling (FR-005) | Fast-follow PI | Requires a corpus large enough for conflicts to actually occur; premature at pilot scale |
| Source registration self-service workflow (FR-007) | Post-pilot | Two hardcoded sources are sufficient for MVP; a full workflow is only needed once onboarding source #3+ |
| Retrieval reranking (FR-011 rerank step) | Fast-follow PI | Hybrid retrieval quality is sufficient to test the core trust hypothesis at MVP's small corpus size; reranking's marginal benefit grows with corpus size, so it's sequenced with the fast-follow PI rather than held up MVP launch. **Note:** this defers only the reranking *step* — RAG evaluation itself (the ability to measure retrieval quality) is in MVP scope per §3 above, precisely so this deferral decision and future reranking work both have a quality baseline to compare against |
| Knowledge graph / GraphRAG (FEAT-13) | Phase 4+, post-PI-3 | Unchanged from original scope — relational query needs haven't been validated as a pilot-stage requirement; revisit if Phase 0/1 user feedback surfaces relationship-shaped questions vector retrieval can't answer |
| Model/System Card publication (FR-013) | Fast-follow PI | Requires at least one real `EvaluationRun` history to be meaningful; MVP's automated eval (§3) produces that history, making this a natural fast-follow rather than a parallel-track item |

**Revision note:** the original version of this table deferred automated evaluation-harness work to "manual sign-off" at MVP and full automation after. That has been revised — see §3 above — because manual sign-off provides no regression protection once real users depend on the MVP, and the cost of automating RAGAS-based evaluation against a small, fixed MVP corpus is low relative to the risk of shipping an ungated retrieval change into a live pilot.

## 5. MVP success criteria (go/no-go for full Program Backlog investment)

| Criterion | Threshold |
|---|---|
| Median time-to-answer reduction (in-scope query types) | ≥25% (lower than the full-product 40% target in [Problem Statement §5.2](../PRODUCT_PROBLEM_STATEMENT.md#52-measurable-business-outcomes) — MVP is a leading indicator, not the final target) |
| Answer groundedness (manual review against MVP query sample) | ≥85% |
| User preference over current search habit (concierge-style A/B or self-report) | ≥50% of sampled interactions |
| Zero permission-enforcement violations found in security review of MVP usage | Hard gate — any violation blocks progression regardless of other metrics |

## 6. MVP as an architectural down-payment, not a throwaway

Unlike the concierge-style prototype in [Problem/Solution Fit](PROBLEM_SOLUTION_FIT.md), this MVP is built on the real target architecture (trust-boundary service split, real retrieval index, real permission enforcement) — it is a true subset of the [Application Architecture](../04-solution-architecture/APPLICATION_ARCHITECTURE.md), not a disposable spike. This is a deliberate Lean tradeoff: the riskiest assumption at this stage is user trust/adoption, not technical feasibility, so the MVP invests in production-grade retrieval and security from the start rather than building throwaway infrastructure that would need to be rebuilt to reach the pilot's own acceptance criteria (§9.4 permission risk in the Problem Statement is a hard constraint even at MVP scale).

## 7. Relationship to delivery planning

MVP scope corresponds to **PI-1** in [PI_PLANNING_OBJECTIVES.md](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md) and the first funding horizon in [EPIC_HYPOTHESIS.md](../06-agile-delivery/EPIC_HYPOTHESIS.md).
