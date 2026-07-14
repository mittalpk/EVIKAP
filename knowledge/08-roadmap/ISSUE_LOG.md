# Issue Log

**Status:** Living document · **Version:** 1.0 · 2026-07-14
**Related:** [EXECUTION_RUNBOOK.md](EXECUTION_RUNBOOK.md) · [../07-governance-risk/RISK_REGISTER.md](../07-governance-risk/RISK_REGISTER.md)

---

## 1. Purpose and how this differs from the Risk Register

The [Risk Register](../07-governance-risk/RISK_REGISTER.md) is **forward-looking** — risks anticipated before they happen, scored and mitigated in advance. This log is **backward-looking** — a record of things that actually went wrong (or were actually discovered) while doing the work, when they were found, and how they were resolved. A risk that materializes becomes an issue here; an issue that reveals a new class of risk should be added to the Risk Register too, but the two lists are not the same list.

## 2. How to log an issue

Add a new entry at the top of Section 3 (most recent first) with the next sequential ID. Every entry needs: what happened, when, how severe, current status, and what resolved it (or what's blocking resolution). Link back to the [Execution Runbook](EXECUTION_RUNBOOK.md) task it was found during, if applicable.

## 3. Log

### ISSUE-010
**Date found:** 2026-07-14 · **Severity:** Low · **Status:** Open
**Found during:** Runbook §4.2 (Data layer)
**Description:** `docs/deployment/deployment_plan.md` documents a working Supabase/Postgres connection (`"✓ Settings initialized: DATABASE_URL loaded"`), but `backend/requirements.txt` has no `sqlalchemy`/`asyncpg`/`psycopg2` dependency — the codebase cannot actually make this connection today. Same "documented but not implemented" pattern already flagged for the Azure deployment doc's database source.
**Resolution / next step:** Not yet fixed. Tracked as part of FEAT-12 database work in [Program Backlog](../06-agile-delivery/PROGRAM_BACKLOG.md); also logged in [Risk Register](../07-governance-risk/RISK_REGISTER.md#3-risks-explicitly-inherited-from-the-current-state-technical-audit) so it isn't lost between documents.

### ISSUE-009
**Date found:** 2026-07-14 · **Severity:** High · **Status:** Fixed
**Found during:** CI/CD update task
**Description:** The GitHub Actions workflow (`deploy.yml`) built and deployed all three services straight to production Azure Container Apps on every push to `main`, with no test step anywhere in the pipeline — the existing (good) pytest suites never ran before a deploy.
**Resolution:** Replaced `deploy.yml` with `ci.yml`: Azure login/GHCR-push/`az containerapp` deploy steps removed entirely; three independent, path-filtered jobs added (`backend-test`, `agent-test`, `frontend-validate`) running pytest and `tsc`+build. Verified locally: 11 backend tests, 5 agent tests, and a clean frontend build all pass via the exact commands the workflow uses. Note: this is a **build/test** gate, not yet the **evaluation-harness** (retrieval/prompt/model quality) gate — that remains open, see Execution Runbook §4.4.

### ISSUE-008
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** "Validate all documents are clean for public repo" review
**Description:** `backend/app/config.py` hardcoded a real Azure AD tenant ID as a Pydantic settings default (`azure_tenant_id: str = "78e7f11a-..."`). Confirmed as a real value (not a public well-known ID, unlike the neighboring `azure_client_id` which is Microsoft's well-known public Azure CLI client ID).
**Resolution:** Default cleared to `""`; neighboring client ID left unchanged with a comment noting why it's safe to keep.

### ISSUE-007
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** Same review as ISSUE-008
**Description:** Both `backend/app/config.py` and `agent/app/config.py` hardcoded a real, live, publicly-resolvable Container App hostname (`*.gentlesea-072b973e.francecentral.azurecontainerapps.io`) as the default CORS `allowed_origins` / backend URL — both in application source code and duplicated in `.github/workflows/deploy.yml`.
**Resolution:** Source defaults cleared to empty (must be set via env var); CI workflow parameterized via `secrets.BACKEND_URL` / `secrets.AGENT_SERVICE_URL`. Re-ran the backend/agent test suites after the change — all 16 tests still passed, confirming nothing depended on the hardcoded default.

### ISSUE-006
**Date found:** 2026-07-14 · **Severity:** Low · **Status:** Fixed
**Found during:** Same review as ISSUE-008
**Description:** `terraform/variables.tf` defaulted `github_repo_owner` to `pkmittal`, which doesn't match this repo's actual GitHub remote owner (`mittalpk`) — a stale/inconsistent reference, not itself sensitive but confusing.
**Resolution:** Default replaced with a generic `your-github-username` placeholder.

### ISSUE-005
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** Same review as ISSUE-008
**Description:** `docs/deployment/AZURE_DEPLOYMENT.md` contained real local filesystem paths (`/home/pkmittal/MyProjects/SecureAgentRuntime/OmegaNexus/...`) that leaked both a real username and the name of a different, private/unreleased project (`SecureAgentRuntime`) this codebase originated from.
**Resolution:** Paths replaced with generic `/path/to/OmegaNexus`.

### ISSUE-004
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** Same review as ISSUE-008
**Description:** A real Azure subscription ID (`ecc63471-f21a-46af-a01f-2db799285343`) was hardcoded across four files: `.github/workflows/deploy.yml`, `terraform/fix_state.sh`, `terraform/import_secrets.sh`, `docs/deployment/AZURE_DEPLOYMENT.md`. Not a credential, but real infrastructure-reconnaissance information (also reveals the Key Vault naming pattern `kv-omega-nexus-ecc63471`).
**Resolution:** Workflow parameterized via `secrets.AZURE_SUBSCRIPTION_ID` and `secrets.KEY_VAULT_NAME`; shell scripts changed to require the value as an environment variable (`${SUB_ID:?...}`) instead of hardcoding it; doc changed to a placeholder.

### ISSUE-003
**Date found:** 2026-07-14 · **Severity:** Low · **Status:** Fixed
**Found during:** Credential-leak remediation (see ISSUE-001)
**Description:** `terraform/.terraform.tfstate.lock.info` was tracked in git — contains a local username and hostname (low sensitivity) but shouldn't be version-controlled regardless.
**Resolution:** Untracked via `git rm --cached`; `.gitignore` pattern broadened (see ISSUE-002) to prevent recurrence.

### ISSUE-002
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** Credential-leak remediation (see ISSUE-001) — root cause analysis
**Description:** `.gitignore` had a pattern `*.tfstate.backup`, which does not match a timestamped filename like `terraform.tfstate.1774373141.backup` (the timestamp sits *between* `.tfstate` and `.backup`, breaking the glob). This is the exact reason ISSUE-001 was possible.
**Resolution:** Pattern broadened to `*.tfstate.*` (in addition to the existing patterns), which matches timestamped variants.

### ISSUE-001
**Date found:** 2026-07-14 · **Severity:** Critical · **Status:** Mitigated (rotation still pending — see Execution Runbook §4.1)
**Found during:** Initial repository audit ([`docs/OMEGA_NEXUS_AUDIT.md`](../OMEGA_NEXUS_AUDIT.md))
**Description:** `terraform/terraform.tfstate.1774373141.backup` was committed to git and contained real, non-placeholder values for the Gemini API key and GitHub PAT (captured via `azurerm_key_vault_secret` resources in the state file). The file had already been pushed to the public `origin/main` remote.
**Resolution:** History rewritten with `git-filter-repo --path terraform/terraform.tfstate.1774373141.backup --invert-paths`; `.gitignore` fixed (ISSUE-002); force-pushed to `origin/main` with explicit user confirmation. **Still open:** the actual Gemini API key and GitHub PAT must be rotated in their respective consoles — a history rewrite does not undo exposure that already happened, and this action requires human access to external systems an agent cannot reach.

## 4. Summary by status

| Status | Count |
|---|---|
| Fixed | 8 |
| Mitigated (partial — human action still required) | 1 |
| Open | 1 |
