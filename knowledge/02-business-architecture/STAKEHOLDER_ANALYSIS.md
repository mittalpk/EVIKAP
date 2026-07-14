# Stakeholder Analysis

**TOGAF ADM Phase B (Stakeholder Management) / BABOK Stakeholder Analysis**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../PRODUCT_PROBLEM_STATEMENT.md §4](../PRODUCT_PROBLEM_STATEMENT.md#4-stakeholder-analysis)

---

## 1. Purpose

Expands the summary stakeholder table in the Problem Statement into a power/interest-mapped, engagement-planned register suitable for architecture governance and delivery planning.

## 2. Power/interest grid

| Stakeholder | Power over outcome | Interest level | Engagement strategy |
|---|---|---|---|
| Budget owner (CTO / Head of AI Platform) | High | High | Manage closely — monthly steering review against KPIs |
| Enterprise/security architecture board | High | Medium | Keep satisfied — formal review gates at each TOGAF phase |
| Pilot business unit sponsor | Medium-High | High | Manage closely — weekly during pilot |
| CISO / data governance office | High (veto on go-live) | Medium | Keep satisfied — early and continuous involvement, not a late gate |
| Platform/AI engineering team (delivery) | Medium | High | Manage closely — daily/sprint cadence |
| Source system owners (repo, wiki, DB admins) | Medium (can block source access) | Low-Medium | Keep informed, consult at source-onboarding time |
| End users — knowledge workers | Low (individually), High (collectively via adoption) | High | Keep informed, close feedback loop post-launch |
| AI agent/consumer teams (coding assistant, support copilot owners) | Low-Medium | High | Manage closely — they are the machine-consumer stakeholder and the interface contract must serve them |
| Legal / compliance | Medium | Medium | Consult at data-classification and audit-design stages |

## 3. Stakeholder needs and success criteria (detailed)

### 3.1 Budget owner (CTO / Head of AI Platform)

- **Needs:** confidence the investment reduces risk while enabling the broader AI roadmap, at a justified and trending-down cost per query.
- **Success criteria:** validated ROI model (see [Problem Statement §5.4](../PRODUCT_PROBLEM_STATEMENT.md#54-expected-roi)) confirmed against pilot data before enterprise-wide funding is approved.
- **Primary artifact:** [../06-agile-delivery/EPIC_HYPOTHESIS.md](../06-agile-delivery/EPIC_HYPOTHESIS.md)

### 3.2 Enterprise/security architecture board

- **Needs:** assurance the architecture follows organizational standards and does not introduce ungoverned data-access paths.
- **Success criteria:** formal sign-off at each TOGAF phase gate; zero unresolved high-severity architecture review findings.
- **Primary artifact:** [../07-governance-risk/ARCHITECTURE_GOVERNANCE.md](../07-governance-risk/ARCHITECTURE_GOVERNANCE.md)

### 3.3 Pilot business unit sponsor

- **Needs:** a system their team will actually use, with visible time-to-answer improvement within the pilot window.
- **Success criteria:** ≥40% reduction in median time-to-answer; formal attestation per [Problem Statement §11.1](../PRODUCT_PROBLEM_STATEMENT.md#111-business-acceptance-criteria).
- **Primary artifact:** [../08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md](../08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md)

### 3.4 CISO / data governance office

- **Needs:** a provable answer to "what can this AI system see, and how do you know."
- **Success criteria:** zero critical/high audit findings on access control; full request-to-evidence audit trail operational before any source containing regulated data is onboarded.
- **Primary artifact:** [../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md)

### 3.5 Platform/AI engineering team

- **Needs:** requirements stable enough to plan sprints against; clear acceptance criteria; not chasing a moving target.
- **Success criteria:** requirements traceability matrix maintained without unmanaged scope creep (see [Requirements Management Plan](../03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md)).
- **Primary artifact:** [../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md)

### 3.6 Source system owners

- **Needs:** confidence that indexing their system will not degrade its performance (API rate limits) or leak content beyond existing access boundaries.
- **Success criteria:** source-connector certification process (see [Compliance & Security Framework](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md)) passed before go-live per source.

### 3.7 End users — knowledge workers

- **Needs:** faster, trustworthy answers without learning a new complex tool.
- **Success criteria:** high perceived trustworthiness (citation-backed answers), low false-answer rate, minimal onboarding friction.
- **Primary artifact:** [../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md — user workflows](../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md)

### 3.8 AI agent/consumer teams

- **Needs:** a stable, well-documented, standards-based (MCP) tool contract they can build against without bespoke integration per agent.
- **Success criteria:** documented API/tool contract with backward-compatible versioning; reliable latency and correct citations for machine consumption.

## 4. RACI summary (key decisions)

| Decision | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Approve architecture vision | AI Solutions Architect | Enterprise Architecture Board | Security, Platform Eng | All stakeholders |
| Approve source onboarding | Platform team | Security engineering | Source system owner, Legal | Compliance |
| Approve pilot go-live | Platform team | Budget owner | CISO, Pilot sponsor | All stakeholders |
| Approve enterprise-wide rollout funding | Product/Program lead | Budget owner | Pilot sponsor, Architecture board | All stakeholders |
| Approve retrieval/prompt/model production change | AI engineering lead | AI engineering lead | — (gated by automated evaluation harness, not manual approval) | Platform team |

## 5. Stakeholder communication cadence

| Audience | Cadence | Format |
|---|---|---|
| Budget owner / steering | Monthly | KPI dashboard review against [Problem Statement §12](../PRODUCT_PROBLEM_STATEMENT.md#12-success-metrics) |
| Architecture board | Per TOGAF phase gate | Formal review package |
| Pilot sponsor | Weekly during pilot | Working session + metrics snapshot |
| Delivery team | Daily / per sprint | Standup, sprint review, PI planning |
| End users | Bi-weekly during pilot, monthly post-GA | In-product feedback prompt + release notes |
