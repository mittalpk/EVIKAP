# Compliance and Security Framework

**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](../03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) · [../04-solution-architecture/DATA_ARCHITECTURE.md §6](../04-solution-architecture/DATA_ARCHITECTURE.md#6-data-classification-and-handling)

---

## 1. Purpose

Defines the concrete controls that make NFR-002 (Security), NFR-003 (Privacy), NFR-004 (Compliance), and NFR-012 (Governance and transparency) provable, not just stated — what a CISO or auditor needs to see before signing off on production use.

This framework's governance posture is mapped to **NIST AI Risk Management Framework (AI RMF)** as the primary reference and **ISO/IEC 42001** (AI management systems) as a secondary alignment target, rather than internal policy alone — per NFR-012, this mapping is reviewed at least annually (see §5) and its concrete evidence artifact is the Model/System Card (FR-013) published per production release.

## 2. Control framework

| Control area | Requirement | Verification evidence |
|---|---|---|
| Identity & access | Enterprise SSO/OIDC integration for all human users; service-identity credentials for all agent consumers; no shared/generic accounts | IdP integration test; access review confirming no shared credentials in use |
| Least privilege | Each source connector holds only the minimum scope needed to read (never write) its source system | Per-connector credential scope audit at onboarding |
| Trust boundary | No AI reasoning component holds source-system credentials (architecture principle, [Architecture Vision §7](../01-architecture-vision/ARCHITECTURE_VISION.md#7-architecture-principles)) | Static analysis: no source-system SDK imports in the orchestration service |
| Secrets management | All secrets in a managed vault with rotation policy; no secrets in source control, container images, or Terraform state committed to version control | Repository scan (secret-scanning); the corrective action already taken during the technical audit (purging a committed Terraform state backup and broadening the `.gitignore` pattern) is the template for this control going forward |
| Authentication integrity | All credential comparisons constant-time; no plaintext credential comparison anywhere in the codebase | Static analysis / code review checklist item |
| Permission propagation | Retrieval never surfaces content beyond what the requester could access at the source | Permission-matrix test suite per connector (see [Risk Register RISK-002](RISK_REGISTER.md)) |
| Data classification | Every registered source is classified (public / internal-sensitive / regulated) before indexing | Source registration record (FR-007) requires a classification field; unclassified sources cannot be indexed |
| PII/regulated data handling | Regulated sources are not onboarded until redaction and audit controls for that source type are verified, implemented via a named PII-detection library (Microsoft Presidio) rather than ad hoc pattern matching | Compliance sign-off gate, tracked in [Architecture Governance §3](ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals) |
| Prompt-injection defense | Retrieved source content is scanned by the guardrails service (Guardrails AI or NVIDIA NeMo Guardrails, FR-012) before it reaches the synthesis model; synthesized output is validated before delivery | Maintained prompt-injection fixture test suite passing in CI (FEAT-17) |
| AI quality assurance | Every retrieval/prompt/model change is evaluated against a versioned golden dataset (RAGAS primary, DeepEval fallback) before production rollout (NFR-011) | CI evaluation-gate audit; production quality-trend dashboard reviewed at each PI boundary |
| AI governance transparency | Every production pipeline version has a current, published Model/System Card (FR-013) whose eval scores match the evaluation harness's own record | Spot-check audit per NFR-012; card absence or score mismatch blocks release sign-off |
| Audit trail | Every query, requester identity, evidence used, and answer is logged and retrievable | FR-008; compliance reviewer walkthrough test (can they answer "who saw what, when" from logs alone) |
| Rate limiting / abuse prevention | Public-facing endpoints (login, query) are rate-limited | Load/abuse test confirming throttling behavior |
| Model training data governance | No source content used to train/fine-tune shared models without explicit consent | Data-lineage audit of any model training pipeline |
| CI/CD supply chain | No deploy without passing tests and evaluation gate; container images built from pinned, scanned base images | CI pipeline configuration review |

## 3. Regulatory considerations

The applicable regulatory framework depends on the sponsoring organization's industry and geography and must be confirmed during discovery (per [Problem Statement §9.3](../PRODUCT_PROBLEM_STATEMENT.md#93-regulatory-considerations)). This framework is designed to satisfy the common denominator across likely frameworks:

- **Data residency** — source connectors and the retrieval index must respect any data-residency constraint already governing the underlying source system; Omega Nexus does not introduce a new residency boundary.
- **Right to audit AI-mediated data access** — directly satisfied by FR-008 and the audit-trail control above; this is the specific capability increasingly expected under AI-governance frameworks (e.g., EU AI Act–aligned expectations referenced in [Problem Statement §3.4](../PRODUCT_PROBLEM_STATEMENT.md#34-market-trends-driving-the-need-for-ai)).
- **Data minimization** — the retrieval index stores derived representations (embeddings, chunk metadata) of source content, not a parallel unrestricted copy; deletion propagation (see [Data Architecture §7](../04-solution-architecture/DATA_ARCHITECTURE.md#7-data-quality-and-lifecycle)) ensures the index does not outlive the source's own access controls.

## 4. Incident response posture

| Scenario | Response |
|---|---|
| Suspected over-exposure via a permission-propagation defect | Immediately disable the affected source connector; audit log review to determine blast radius; notify Compliance per organizational incident policy |
| Leaked credential (source connector or LLM provider key) | Rotate immediately; purge from any version-controlled artifact (state files, config); review `.gitignore`/secret-scanning coverage for the gap that allowed it — this is the exact remediation pattern already exercised once during the pre-delivery technical audit and is treated as the standing playbook, not a one-off |
| Evaluation harness detects a groundedness regression in production | Automatic rollback of the offending retrieval/prompt/model change per the CI gate (NFR-010); no manual override without documented sign-off |

## 5. Ongoing compliance cadence

| Activity | Frequency |
|---|---|
| Access-control audit (permission-matrix re-verification) | Quarterly, and at every new source-connector onboarding |
| Secret rotation | Per organizational policy, minimum annually or immediately on suspected compromise |
| Penetration test | Before enterprise-wide rollout (Gate 3), then annually |
| Compliance walkthrough (audit log usability test) | Before any regulated-data source onboarding, then semi-annually |
| NIST AI RMF / ISO 42001 mapping review | Annually (minimum), or on any material architecture change |
| Model/System Card spot-check (scores match evaluation harness) | Per production release, sampled quarterly for audit purposes |
