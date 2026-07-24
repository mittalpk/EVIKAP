# VigilRAG User Stories Backlog

**Status:** Active · **Version:** 1.0 · 2026-07-20  
**Branch:** `feature/user-stories-backlog`  
**Related:** [EXECUTION_RUNBOOK.md](../EXECUTION_RUNBOOK.md) · [MIGRATION_IMPLEMENTATION_ROADMAP.md](../MIGRATION_IMPLEMENTATION_ROADMAP.md) · [../../06-agile-delivery/PROGRAM_BACKLOG.md](../../06-agile-delivery/PROGRAM_BACKLOG.md)

---

## Overview

This folder contains the full decomposed user story backlog for VigilRAG — one `.md` file per story. Stories are derived from the [Functional Requirements Specification](../../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md), [Non-Functional Requirements Specification](../../03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md), and the [Program Backlog](../../06-agile-delivery/PROGRAM_BACKLOG.md), and are sequenced across PI-0 through PI-3.

Each story follows a consistent 16-section template:
**Title · User Story · Description · Business Value · Acceptance Criteria · Functional Requirements · Non-Functional Requirements · Dependencies · Assumptions · Edge Cases · Technical Notes · Definition of Done · Priority · Estimated Effort · Related Epics/Features**

---

## Story Index

### PI-0 — Discovery & Validation

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-001 | [US-001-pilot-bu-identification.md](done/US-001-pilot-bu-identification.md) | Pilot Business Unit Identification & Source-System Access Confirmation | Completed | M |
| US-002 | [US-002-time-motion-survey.md](done/US-002-time-motion-survey.md) | Time-Motion Survey & Knowledge Fragmentation Baseline | Completed | M |
| US-003 | [US-003-concierge-prototype-validation.md](done/US-003-concierge-prototype-validation.md) | Concierge Prototype Validation Run | Completed | M |
| US-004 | [US-004-security-architecture-design-spike.md](done/US-004-security-architecture-design-spike.md) | Security Architecture Design Spike — Permission Enforcement | Completed | M |

---

### PI-1 — Foundation & MVP

#### Data Layer (FEAT-02 enabler)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-005 | [US-005-postgres-provisioning.md](done/US-005-postgres-provisioning.md) | Supabase/Postgres Project Provisioning & Database Migration | Completed | S |
| US-006 | [US-006-github-connector-embedding-ingestion.md](done/US-006-github-connector-embedding-ingestion.md) | GitHub Source Connector — Embedding Ingestion Pipeline | Completed | L |
| US-007 | [US-007-wiki-connector-embedding-ingestion.md](done/US-007-wiki-connector-embedding-ingestion.md) | Wiki Source Connector — Embedding Ingestion Pipeline | Completed | M |
| US-008 | [US-008-hybrid-retrieval-endpoint.md](done/US-008-hybrid-retrieval-endpoint.md) | Hybrid Semantic + Keyword Retrieval Endpoint | Completed | L |
| US-009 | [US-009-retrieval-quality-golden-dataset.md](done/US-009-retrieval-quality-golden-dataset.md) | Retrieval Quality — Golden Dataset & Done-Check | Completed | M |

#### Unified Query Interface (FEAT-01)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-010 | [US-010-query-submission-ui.md](done/US-010-query-submission-ui.md) | Query Submission UI — Basic Input & Response Display | Completed | M |
| US-011 | [US-011-api-query-endpoint.md](done/US-011-api-query-endpoint.md) | API Query Endpoint (POST /api/v1/query) — Agent Orchestration Tier | Completed | L |


#### Provenance & Citations (FEAT-03)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-012 | [US-012-citation-rendering.md](done/US-012-citation-rendering.md) | Citation Rendering — Inline Source Links per Answer Claim | Completed | S |

| US-013 | [US-013-evidence-item-groundedness-tracking.md](done/US-013-evidence-item-groundedness-tracking.md) | EvidenceItem Entity & Groundedness Score Tracking | Completed | M |


#### Permissions & Auth (FEAT-06, FEAT-11)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-014 | [US-014-permission-aware-retrieval.md](done/US-014-permission-aware-retrieval.md) | Permission-Aware Retrieval — Source ACL Enforcement | High | L | Completed |


| US-015 | [US-015-permission-matrix-test-suite.md](done/US-015-permission-matrix-test-suite.md) | Permission Matrix Test Suite — Code & Wiki Sources | Completed | M |

| US-016 | [US-016-rbac-foundation.md](done/US-016-rbac-foundation.md) | RBAC Foundation — Replace Single Hardcoded Admin | Completed | M |

| US-017 | [US-017-jwt-authentication-multi-user.md](US-017-jwt-authentication-multi-user.md) | JWT Authentication — Multi-User Token Flow | High | M |

#### Audit Log (FEAT-08)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-018 | [US-018-minimal-audit-log.md](US-018-minimal-audit-log.md) | Minimal Audit Log — Query, Identity, Evidence, Answer | High | M |

#### Feedback Loop (FEAT-09)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-019 | [US-019-feedback-capture.md](US-019-feedback-capture.md) | Thumbs Up / Down Feedback Capture | Medium | S |
| US-020 | [US-020-feedback-evaluation-routing.md](US-020-feedback-evaluation-routing.md) | Feedback → Evaluation Dataset Routing | Medium | M |

#### RAG Evaluation Harness (FEAT-16)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-021 | [US-021-ragas-evaluation-setup.md](US-021-ragas-evaluation-setup.md) | RAGAS Evaluation Setup & Golden Dataset Bootstrap | High | M |
| US-022 | [US-022-evaluation-run-dashboard.md](US-022-evaluation-run-dashboard.md) | EvaluationRun Record Persistence & Quality Trend Dashboard | High | S |
| US-023 | [US-023-ci-gated-evaluation.md](US-023-ci-gated-evaluation.md) | CI-Gated Evaluation — Block Merge on RAGAS Regression | High | M |

#### Guardrails (FEAT-17)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-024 | [US-024-prompt-injection-defense.md](US-024-prompt-injection-defense.md) | Prompt-Injection Defense — Retrieved Content Scan | High | M |
| US-025 | [US-025-output-validation.md](US-025-output-validation.md) | Output Validation — Structural / Safety Schema Check | High | S |
| US-026 | [US-026-pii-redaction-presidio.md](US-026-pii-redaction-presidio.md) | PII Redaction — Microsoft Presidio Integration | High | M |
| US-027 | [US-027-guardrails-ci-test-suite.md](US-027-guardrails-ci-test-suite.md) | Guardrails CI Test Suite — Injection & Safety Fixture Suite | High | M |

#### Platform Hardening — PI-1 slice (FEAT-11)

| ID | File | Title | Priority | Effort |
|---|---|---|---|---|
| US-028 | [US-028-opentelemetry-tracing.md](US-028-opentelemetry-tracing.md) | OpenTelemetry Tracing — Basic Observability Setup | Medium | M |

---

### PI-2 — Full Requirements Conformance

| ID | File | Title | Feature | Priority | Effort |
|---|---|---|---|---|---|
| US-029 | [US-029-iterative-reasoning-loop.md](US-029-iterative-reasoning-loop.md) | Iterative Multi-Agent Reasoning Loop (Real Evaluate / Re-Plan) | FEAT-04 | High | L |
| US-030 | [US-030-freshness-conflict-signaling.md](US-030-freshness-conflict-signaling.md) | Freshness Detection & Conflict Signaling | FEAT-05 | Medium | M |
| US-031 | [US-031-source-registration-workflow.md](US-031-source-registration-workflow.md) | Source Registration Self-Service Workflow (Admin UI) | FEAT-07 | Medium | L |
| US-032 | [US-032-database-source-connector.md](US-032-database-source-connector.md) | Structured/Database Source Connector (Postgres Schema) | FEAT-12 | High | M |
| US-033 | [US-033-retrieval-reranking.md](US-033-retrieval-reranking.md) | Retrieval Reranking — Cross-Encoder Step | FEAT-18 | Medium | M |
| US-034 | [US-034-model-system-card-publication.md](US-034-model-system-card-publication.md) | Model / System Card Publication | FEAT-19 | Medium | M |
| US-035 | [US-035-terraform-network-drift.md](US-035-terraform-network-drift.md) | Terraform / Network Drift Reconciliation | FEAT-11 | High | M |
| US-036 | [US-036-cost-dashboard-chaos-reliability.md](US-036-cost-dashboard-chaos-reliability.md) | Full Observability — Cost Dashboard, SLO Monitoring, Load Test & Chaos-Tested Reliability | FEAT-11 | High | L |
| US-039 | [US-039-full-compliance-audit-log.md](US-039-full-compliance-audit-log.md) | Full Compliance-Grade Audit Log — Retention, Export & Scheduled Reports | FEAT-08 | High | L |

---

### PI-3 — Platform Expansion

| ID | File | Title | Feature | Priority | Effort |
|---|---|---|---|---|---|
| US-037 | [US-037-mcp-agent-tool-interface.md](US-037-mcp-agent-tool-interface.md) | MCP-Based Agent Tool Interface | FEAT-10 | High | M |
| US-038 | [US-038-vector-db-graduation.md](US-038-vector-db-graduation.md) | Vector Database Graduation Evaluation & Migration | FEAT-20 | Trigger-based | XL/S |

---

## Summary Statistics

| PI | Stories | Total Effort |
|---|---|---|
| PI-0 | 4 | ~14–24 days |
| PI-1 | 24 | ~50–85 days |
| PI-2 | 9 | ~33–60 days |
| PI-3 | 2 | ~4–17 days |
| **Total** | **39** | **~101–186 days** |

---

## Backlog Governance

- Stories are refined at each sprint planning session using WSJF at the story level (per [Program Backlog §6](../../06-agile-delivery/PROGRAM_BACKLOG.md#6-backlog-governance)).
- A story is not "done" unless: it passes its acceptance criteria, does not violate the trust-boundary principle, passes the CI evaluation gate (from PI-1 onward), and is observable in production per NFR-007.
- New stories are added with the next sequential ID (US-039, US-040, …). IDs are stable — retired stories are marked `[RETIRED]` in this index, not renumbered.
- Blockers found while implementing a story are logged in [ISSUE_LOG.md](../ISSUE_LOG.md) before moving on.

## FR / NFR Traceability

| Requirement | Covered by |
|---|---|
| FR-001 | US-010, US-011 |
| FR-002 | US-006, US-007, US-008, US-009, US-032 |
| FR-003 | US-012, US-013 |
| FR-004 | US-011 (stub), US-029 (real) |
| FR-005 | US-030 |
| FR-006 | US-014, US-015, US-016 |
| FR-007 | US-031 |
| FR-008 | US-013, US-018 (PI-1 minimal), US-039 (PI-2 full compliance-grade) |
| FR-009 | US-019, US-020 |
| FR-010 | US-037 |
| FR-011 | US-008 (hook), US-033 (real) |
| FR-012 | US-024, US-025, US-026, US-027 |
| FR-013 | US-034 |
| NFR-001 | US-036 (5× load test), US-038 (architecture graduation) |
| NFR-002 | US-014, US-015, US-016, US-017, US-035, US-039 |
| NFR-003 | US-026 (PII redaction + training data-lineage check) |
| NFR-004 | US-013, US-018 (PI-1), US-039 (PI-2 full + compliance sign-off) |
| NFR-005 | US-036 (chaos test) |
| NFR-006 | US-008, US-028, US-033, US-036 (load test) |
| NFR-007 | US-028, US-036 |
| NFR-008 | US-036 (SLO dashboard + availability alerting) |
| NFR-009 | US-028 (token cost capture), US-036 (cost dashboard) |
| NFR-010 | US-023 (CI gate) |
| NFR-011 | US-021, US-022, US-023 |
| NFR-012 | US-034 (model cards + annual governance review scheduling) |
