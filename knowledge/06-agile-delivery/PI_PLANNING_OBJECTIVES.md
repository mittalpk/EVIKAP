# Program Increment Planning Objectives

**SAFe — PI Objectives**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [PROGRAM_BACKLOG.md](PROGRAM_BACKLOG.md) · [../08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md](../08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md)

---

## 1. Purpose

Translates the Program Backlog into committed, business-value-scored PI objectives, per standard SAFe PI planning output. Each PI is ~8–10 weeks. Objectives are stated as outcomes, not tasks.

## 2. PI-0 — Discovery & Validation (not a build PI)

**Duration:** ~6 weeks. **Funding gate:** [Epic Hypothesis — Gate 0](EPIC_HYPOTHESIS.md#staged-funding-gates-lean-startup-discipline-applied-to-safe-funding).

| Objective | Business value (1–10) | Stretch? |
|---|---|---|
| Complete problem-validation interviews and time-motion survey (Problem/Solution Fit §2) | 8 | No |
| Complete concierge-style solution validation test (Problem/Solution Fit §3) | 9 | No |
| Complete security architecture review of permission-enforcement design for code + wiki sources | 9 | No |
| Publish discovery-phase baseline metrics replacing directional industry benchmarks | 7 | No |

**PI-0 exit gate:** all four objectives met per [Problem/Solution Fit §5](../05-lean-product/PROBLEM_SOLUTION_FIT.md#5-what-fit-looks-like-exit-criteria-for-this-phase).

## 3. PI-1 — MVP (Trust & Adoption Validation)

**Duration:** ~8–10 weeks. **Funding gate:** Gate 1.
**Theme:** prove the trust/adoption hypothesis on real content with a production-grade (if narrow) trust boundary.

| Objective | Business value (1–10) | Stretch? |
|---|---|---|
| FEAT-01 Unified query interface live for pilot users | 8 | No |
| FEAT-02 Hybrid retrieval live for code + wiki sources | 9 | No |
| FEAT-03 Every answer carries verifiable citations | 9 | No |
| FEAT-06 Permission-aware retrieval passes security sign-off before any real content is indexed | 10 | No |
| FEAT-08 Minimal audit log operational | 7 | No |
| FEAT-09 Feedback capture operational, feeding evaluation dataset bootstrap | 6 | No |
| FEAT-11 (slice) CI test gate blocks bad deploys | 8 | No |
| FEAT-16 RAG evaluation harness (RAGAS) operational and CI-gated | 9 | No |
| FEAT-17 Guardrails (prompt-injection defense + PII redaction) operational before real content is indexed | 10 | No |
| Achieve MVP success criteria (MVP Definition §5) | 10 | No |

**PI-1 exit gate:** [MVP success criteria](../05-lean-product/MVP_DEFINITION.md#5-mvp-success-criteria-gono-go-for-full-program-backlog-investment) met, reviewed at Gate 2 decision point.

## 4. PI-2 — Full Requirements Conformance

**Duration:** ~8–10 weeks. **Funding gate:** Gate 2 (contingent on PI-1 exit).
**Theme:** convert the validated MVP into a system meeting the complete functional and non-functional requirement baseline.

| Objective | Business value (1–10) | Stretch? |
|---|---|---|
| FEAT-04 Genuine iterative multi-agent reasoning operational, outperforming single-pass baseline on multi-hop eval subset | 9 | No |
| FEAT-05 Freshness/conflict signaling operational | 6 | Yes |
| FEAT-07 Self-service source registration workflow | 6 | Yes |
| FEAT-12 Structured/database source connector | 7 | No |
| FEAT-11 (remainder) Full observability, cost dashboards, chaos-tested reliability | 8 | No |
| FEAT-18 Retrieval reranking operational, measurable top-k relevance improvement over no-rerank baseline | 6 | Yes |
| FEAT-19 Model/System Card published for the PI-2 release, scores matching the evaluation harness record | 6 | Yes |
| Groundedness rate ≥90% on full golden evaluation dataset | 10 | No |
| Terraform/runtime network drift resolved before any regulated-data source is considered | 9 | No |
| FEAT-20 vector database graduation trigger criteria evaluated (Technology Architecture §6a) — migrate only if ≥2 signals met | 5 | Yes |

**PI-2 exit gate:** full [Acceptance Criteria](../PRODUCT_PROBLEM_STATEMENT.md#11-acceptance-criteria) met; business case validated against pilot-measured (not benchmark) ROI per [Epic Hypothesis](EPIC_HYPOTHESIS.md#lean-business-case).

## 5. PI-3 — Platform Expansion (Machine Consumers)

**Duration:** ~8–10 weeks. **Funding gate:** Gate 3 (contingent on PI-2 exit and enterprise-rollout approval).
**Theme:** extend the validated, hardened platform to AI-agent (machine) consumers and prepare for scale beyond the pilot business unit.

| Objective | Business value (1–10) | Stretch? |
|---|---|---|
| FEAT-10 MCP-based agent tool interface live, validated against a reference external agent | 8 | No |
| Load-tested to enterprise-scale volume (NFR-001) | 8 | No |
| Multi-provider model routing/fallback operational (NFR-009, reliability) | 7 | No |
| Enterprise-wide rollout plan approved by budget owner | 9 | No |

## 6. Program risks tracked across PIs

See [../07-governance-risk/RISK_REGISTER.md](../07-governance-risk/RISK_REGISTER.md) — reviewed and updated at every PI boundary as a standing PI planning agenda item.

## 7. Definition of Done (applies to every PI)

A feature is not "done" unless: it passes its acceptance criteria, it does not violate the trust-boundary principle ([Architecture Vision §7](../01-architecture-vision/ARCHITECTURE_VISION.md#7-architecture-principles)), it passes the CI evaluation gate (once FEAT-11's CI gate exists, from PI-1 onward), and it is observable in production per NFR-007.
