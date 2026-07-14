# Risk Register

**TOGAF Phase H-adjacent / SAFe program risk tracking**
**Status:** Living document · **Version:** 1.0 · 2026-07-14
**Review cadence:** every PI boundary (see [PI_PLANNING_OBJECTIVES.md §6](../06-agile-delivery/PI_PLANNING_OBJECTIVES.md#6-program-risks-tracked-across-pis))

---

## 1. Scoring model

**Likelihood** (1–5) × **Impact** (1–5) = **Score** (1–25). Score ≥15 requires an active mitigation owner and PI-level tracking; score <10 is monitored only.

## 2. Register

| ID | Risk | Likelihood | Impact | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| RISK-001 | Source content quality is inconsistent/stale, degrading retrieval trust | 4 | 4 | 16 | Freshness/conflict signaling (FR-005); source-owner feedback loop | Platform team |
| RISK-002 | Permission propagation is incorrectly implemented for a source type, causing over-exposure | 3 | 5 | 15 | Permission-matrix test suite per connector; security architecture review gate before any connector goes live against real content (FEAT-06) | Security engineering |
| RISK-003 | Users don't trust or adopt synthesized answers, invalidating the core hypothesis | 3 | 5 | 15 | Concierge-style validation before MVP build (Problem/Solution Fit §3); mandatory citations; feedback loop | Product owner |
| RISK-004 | Fragmentation cost, once measured, is materially lower than industry benchmarks, weakening the business case | 3 | 4 | 12 | Discovery-phase baseline measurement before Gate 1 funding (Epic Hypothesis funding gates) | Budget owner / BA |
| RISK-005 | LLM inference cost scales faster than value delivered, eroding ROI | 3 | 4 | 12 | Model routing policy (NFR-009); cost-per-query dashboard reviewed every PI | AI engineering lead |
| RISK-006 | Single LLM provider dependency causes an outage-driven availability breach | 2 | 4 | 8 | Multi-provider fallback (Technology Architecture §3) | Platform team |
| RISK-007 | Regulated data (PII/PHI/financial) is onboarded before redaction/audit controls are ready | 2 | 5 | 10 | Data classification gate at source registration (FR-007); regulated sources blocked until Compliance & Security Framework controls verified | Compliance |
| RISK-008 | Terraform/runtime infrastructure drift (inherited from current build) persists into production, undermining the documented network-isolation posture | 3 | 4 | 12 | Drift resolved as an explicit early PI-2 task (Technology Architecture §6); IaC state reconciliation before any regulated source onboarding | Platform engineering |
| RISK-009 | CI pipeline lacks a test/evaluation gate, allowing a quality or security regression to reach production | 2 | 5 | 10 | Mandatory CI evaluation gate delivered in PI-1 (FEAT-11 + FEAT-16, RAGAS-based, NFR-011); no exceptions without documented sign-off | AI engineering lead |
| RISK-010 | "Multi-agent reasoning" is delivered as marketing language without genuine iterative behavior (repeating the gap identified in the current-state audit) | 2 | 4 | 8 | FEAT-04 acceptance criteria explicitly requires outperforming a single-pass baseline on the multi-hop evaluation subset, not just code that "looks like" a state machine | AI engineering lead |
| RISK-011 | Organizational stakeholders treat this as a search feature rather than a governed platform, under-resourcing evaluation/observability infrastructure | 2 | 4 | 8 | Architecture Vision principle #5 ("observability is not optional") is a stated Definition-of-Done item, not optional scope | AI Solutions Architect |
| RISK-012 | Pilot business unit access to representative source systems is delayed, blocking discovery | 2 | 3 | 6 | Confirmed as an explicit PI-0 entry criterion before delivery planning begins | Product owner |
| RISK-013 | Retrieved source content contains an adversarial prompt-injection payload that manipulates the synthesized answer or exfiltrates data via the response | 2 | 5 | 10 | Guardrails service (Guardrails AI / NeMo Guardrails, FR-012, FEAT-17) scans evidence before synthesis and validates output before delivery; maintained injection-fixture test suite in CI | Security engineering |
| RISK-014 | Vector database graduation (FEAT-20) is executed prematurely (wasted engineering effort migrating before it's needed) or too late (production degradation once the corpus outgrows pgvector) | 2 | 3 | 6 | Explicit, evidence-based trigger criteria defined in [Technology Architecture §6a](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path) — migration decision is trigger-based, not calendar-based | Platform engineering |

## 3. Risks explicitly inherited from the current-state technical audit

The following risks are carried forward from [`OMEGA_NEXUS_AUDIT.md`](../OMEGA_NEXUS_AUDIT.md) as known starting conditions, not new discoveries:

- No CI test gate before deploy → RISK-009.
- Fictional database source (advertised, not implemented) → addressed structurally in [Data Architecture §3](../04-solution-architecture/DATA_ARCHITECTURE.md#3-current-state-gap-from-audit); tracked as a scope item (FEAT-12), not a standing risk, once resourced.
- Terraform/runtime network drift → RISK-008.
- Single-pass agent loop marketed as iterative → RISK-010.
- Previously leaked credentials (resolved during the audit engagement via history purge; rotation is an operational action outside this register's scope, but the underlying practice of committing state backups is addressed by the `.gitignore` fix already applied and by [Compliance & Security Framework](COMPLIANCE_SECURITY_FRAMEWORK.md) secret-handling controls).
- The free-tier demo deployment plan (`deployment/deployment_plan.md`) documents a Supabase/Postgres connection that the current `backend/` codebase cannot actually make (no `sqlalchemy`/`asyncpg`/`psycopg2` dependency) — the same "documented but not implemented" pattern as the Azure deployment doc's fictional database source, now tracked identically via [Technology Architecture §6](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6-deployment-profiles) and closed by the same FEAT-12 database work, not as a separate risk item.

## 4. Escalation

Any risk scoring ≥20, or any risk realized as an actual incident regardless of score, is escalated immediately to the budget owner and architecture board outside the normal PI-boundary review cadence, per the RACI in [Stakeholder Analysis §4](../02-business-architecture/STAKEHOLDER_ANALYSIS.md#4-raci-summary-key-decisions).
