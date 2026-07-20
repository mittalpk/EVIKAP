# US-035 — Terraform / Network Drift Reconciliation

## User Story

**As a** Platform Engineer,  
**I want to** reconcile the Terraform-managed VNet/NSG resources with the Container Apps environment so that the network isolation described in the architecture actually matches the running infrastructure,  
**So that** the platform's security posture is real and verifiable, not aspirational, before any regulated-data source is considered.

---

## Description

The [EVIKAP audit](../../EVIKAP_AUDIT.md) and [Risk Register RISK-008](../../07-governance-risk/RISK_REGISTER.md) identified infrastructure drift: the VNet and NSGs provisioned by `terraform/main.tf` are not attached to the Container Apps environment actually running the services (which uses a pre-existing `nexvocab-env-prod` environment from a different project). This story either: (a) wires the new VNet/NSG to the actual Container Apps environment, or (b) removes the unused VNet/NSG resources from Terraform and documents the actual network architecture honestly. The choice between (a) and (b) is a decision for the Architecture Review Board.

---

## Business Value

- Closes RISK-008 — the highest-priority infrastructure risk in the risk register for the enterprise profile.
- Required before any regulated-data source can be onboarded (per [Architecture Governance §3](../../07-governance-risk/ARCHITECTURE_GOVERNANCE.md#3-phase-gate-approvals) gate).
- Makes the security architecture claim ("network-isolated Container Apps") match reality.

---

## Acceptance Criteria

**Given** the current state of Terraform-managed resources and the running Container Apps environment,  
**When** this story is complete,  
**Then:**
- Option A (wire VNet): The running Container Apps environment is associated with the Terraform-managed VNet/NSG; inbound/outbound traffic flows through the NSG rules; Terraform state reflects the live configuration with no drift.
- OR Option B (remove): The unused VNet/NSG resources are removed from Terraform; `terraform plan` shows no changes; the `README.md` and architecture documents accurately describe the actual network configuration (no VNet isolation).
- In either case: `terraform plan` shows zero drift after the reconciliation.
- Compliance review sign-off: the chosen network architecture is reviewed by the Security Engineering team before any regulated-data source is onboarded.

---

## Functional Requirements

- Not a functional requirement — this is an infrastructure correctness story.
- Enables FR-006 (Permission-aware retrieval) for regulated-data sources — but only after this story is complete.

---

## Non-Functional Requirements

- NFR-002 (Security) — the running infrastructure must match the documented security posture.
- NFR-010 (Maintainability) — Terraform state must be clean; no `terraform import` workarounds unless they result in a consistent state.

---

## Dependencies

- Azure subscription access with Contributor role on the Container Apps resource group.
- ARB decision: Option A vs. Option B (document the decision as an ADR before executing).

---

## Assumptions

- Option A (wire VNet) is the preferred outcome for the enterprise deployment profile.
- Option B (remove VNet) is acceptable for the demo deployment profile where network isolation is not an NFR.
- A Terraform state migration (`terraform import` or state move) may be required to attach the existing Container Apps environment to the Terraform-managed VNet.

---

## Edge Cases

- **VNet attachment causes Container App restart:** Schedule during a maintenance window; the pilot is not yet live with real users so downtime impact is limited.
- **`terraform apply` fails midway:** Terraform state may be partially updated; run `terraform refresh` to reconcile before retrying.

---

## Technical Notes / Implementation Considerations

- **Approach:**
  1. Run `terraform plan` to document the current drift.
  2. ARB reviews the plan and selects Option A or B.
  3. If Option A: update `terraform/main.tf` to reference the running Container Apps environment; run `terraform apply`; verify NSG rules are applied.
  4. If Option B: remove VNet/NSG resources from `terraform/main.tf`; run `terraform apply -destroy` for the unused resources; update architecture documentation.
  5. Run `terraform plan` again to confirm zero drift.
  6. Security review sign-off.
- **Documentation update:** Update `knowledge/04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md` and `README.md` to reflect the actual network configuration.

---

## Definition of Done

- [ ] ARB decision (Option A or B) documented as an ADR.
- [ ] `terraform plan` shows zero drift after reconciliation.
- [ ] If Option A: NSG rules confirmed applied to the running Container Apps environment (verified via Azure Portal).
- [ ] If Option B: unused VNet/NSG resources removed; architecture documentation updated.
- [ ] Security Engineering sign-off documented.
- [ ] RISK-008 in the Risk Register updated to "Resolved".

---

## Priority

**High** in PI-2 (required before regulated-data source consideration).

## Estimated Effort

**M (Medium)** — ~2–4 days (Terraform analysis, ARB decision, apply, verification, documentation update).

## Related Epics / Features

- FEAT-11 (Platform hardening — infrastructure drift)
- NFR-002 (Security)
- [RISK-008](../../07-governance-risk/RISK_REGISTER.md)
- Migration Roadmap §5 Phase 2
