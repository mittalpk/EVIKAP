# Omega Nexus — Enterprise Knowledge Base

This folder is the single source of truth for Omega Nexus's business and solution architecture rationale. It is organized around four complementary methodologies, each covering the questions the others don't:

- **TOGAF** — why the architecture exists and how it's governed (`01-architecture-vision`, `02-business-architecture`, `04-solution-architecture`, `07-governance-risk`, `08-roadmap`)
- **BABOK** — what the requirements actually are and how they were elicited (`03-business-analysis`)
- **Lean Product Development** — whether the problem/solution pairing is validated before committing engineering investment (`05-lean-product`)
- **SAFe** — how validated scope becomes funded, sequenced delivery work (`06-agile-delivery`)

## Reading order

| # | Document | Answers |
|---|---|---|
| — | [PRODUCT_PROBLEM_STATEMENT.md](PRODUCT_PROBLEM_STATEMENT.md) | Why does this need to exist at all? |
| — | [OMEGA_NEXUS_AUDIT.md](OMEGA_NEXUS_AUDIT.md) | What does the system actually do today, as opposed to what it claims to do? Read this before §1 — it's the as-is baseline everything else in this folder is measured against. |
| 1 | [01-architecture-vision/ARCHITECTURE_VISION.md](01-architecture-vision/ARCHITECTURE_VISION.md) | What is the target architecture state and why (TOGAF Phase A)? |
| 2 | [02-business-architecture/BUSINESS_ARCHITECTURE.md](02-business-architecture/BUSINESS_ARCHITECTURE.md) | What capabilities and value streams does the business need (TOGAF Phase B)? |
| 2 | [02-business-architecture/STAKEHOLDER_ANALYSIS.md](02-business-architecture/STAKEHOLDER_ANALYSIS.md) | Who cares, and what does each group need to see to say yes? |
| 3 | [03-business-analysis/BUSINESS_ANALYSIS_PLAN.md](03-business-analysis/BUSINESS_ANALYSIS_PLAN.md) | How will requirements be elicited, governed, and traced (BABOK)? |
| 3 | [03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md](03-business-analysis/REQUIREMENTS_MANAGEMENT_PLAN.md) | How do requirements get approved, changed, and traced to delivery? |
| 3 | [03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) | What must the system do, at a testable level? |
| 3 | [03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) | What quality attributes must the system meet, at a testable level? |
| 4 | [04-solution-architecture/DATA_ARCHITECTURE.md](04-solution-architecture/DATA_ARCHITECTURE.md) | What data exists, where does it live, how does it flow (TOGAF Phase C)? |
| 4 | [04-solution-architecture/APPLICATION_ARCHITECTURE.md](04-solution-architecture/APPLICATION_ARCHITECTURE.md) | What services exist and how do they interact (TOGAF Phase C)? |
| 4 | [04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md](04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md) | What infrastructure and platforms realize the application architecture (TOGAF Phase D)? |
| 4 | [04-solution-architecture/ARCHITECTURE.md](04-solution-architecture/ARCHITECTURE.md) | What does the as-built system actually look like, independent of the target-state docs above? |
| 4 | [04-solution-architecture/deployment/AZURE_DEPLOYMENT.md](04-solution-architecture/deployment/AZURE_DEPLOYMENT.md) | How do I actually deploy the enterprise profile to Azure, step by step? |
| 4 | [04-solution-architecture/deployment/deployment_plan.md](04-solution-architecture/deployment/deployment_plan.md) | How do I actually deploy the low-cost demo profile to Netlify/Koyeb/Supabase, step by step? |
| 5 | [05-lean-product/LEAN_CANVAS.md](05-lean-product/LEAN_CANVAS.md) | Is this a coherent, fundable business model on one page? |
| 5 | [05-lean-product/PROBLEM_SOLUTION_FIT.md](05-lean-product/PROBLEM_SOLUTION_FIT.md) | Is there evidence the problem is real and this solution fits it? |
| 5 | [05-lean-product/MVP_DEFINITION.md](05-lean-product/MVP_DEFINITION.md) | What is the smallest thing that tests the riskiest assumption? |
| 6 | [06-agile-delivery/EPIC_HYPOTHESIS.md](06-agile-delivery/EPIC_HYPOTHESIS.md) | What's the funded bet, and how do we know if it paid off (SAFe Lean Business Case)? |
| 6 | [06-agile-delivery/PROGRAM_BACKLOG.md](06-agile-delivery/PROGRAM_BACKLOG.md) | What features realize the epic, and in what sequence? |
| 6 | [06-agile-delivery/PI_PLANNING_OBJECTIVES.md](06-agile-delivery/PI_PLANNING_OBJECTIVES.md) | What will the first Program Increment actually deliver? |
| 7 | [07-governance-risk/RISK_REGISTER.md](07-governance-risk/RISK_REGISTER.md) | What could go wrong, and what's the mitigation? |
| 7 | [07-governance-risk/ARCHITECTURE_GOVERNANCE.md](07-governance-risk/ARCHITECTURE_GOVERNANCE.md) | Who has authority to approve architecture change, and how is compliance checked? |
| 7 | [07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md](07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md) | What security/compliance posture must be provable, and to whom? |
| 8 | [08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md](08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md) | How do we get from current state to target state (TOGAF Phases E/F)? |
| 8 | [08-roadmap/EXECUTION_RUNBOOK.md](08-roadmap/EXECUTION_RUNBOOK.md) | What's the concrete, ordered task checklist for Phase 0/1 — what do I actually do, in order? |
| 8 | [08-roadmap/ISSUE_LOG.md](08-roadmap/ISSUE_LOG.md) | What actually went wrong during execution, and how was it resolved? |

## Current-state vs. target-state documents

Most of this folder describes a **target** state — what the architecture, requirements, and delivery plan should become. Two documents instead describe **as-is** reality and anchor everything else against it:

- [OMEGA_NEXUS_AUDIT.md](OMEGA_NEXUS_AUDIT.md) — the technical audit of what the system actually does today; the risk baseline for `07-governance-risk` and the gap baseline for `08-roadmap`.
- [04-solution-architecture/ARCHITECTURE.md](04-solution-architecture/ARCHITECTURE.md) — the as-built system architecture description, a companion to (not a replacement for) the target-state `DATA_ARCHITECTURE.md`/`APPLICATION_ARCHITECTURE.md`/`TECHNOLOGY_ARCHITECTURE.md` in the same folder.

Everything in this knowledge base, including these two, lives under `knowledge/` — there is no separate `docs/` folder; superseded material that nothing here references lives outside version control in the untracked `.doc/` archive instead of being deleted outright.

## Conventions

- Every document is a living artifact — update it as decisions change, don't fork a v2 file.
- Cross-references use relative links so this folder is portable if relocated.
- Where a document makes a numeric claim (cost, ROI, benchmark), it is flagged as either **validated** (measured from this organization's own data) or **directional** (industry benchmark pending validation) — never presented as validated fact when it isn't.
