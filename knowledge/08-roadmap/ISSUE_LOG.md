# Issue Log

**Status:** Living document · **Version:** 1.0 · 2026-07-14
**Related:** [EXECUTION_RUNBOOK.md](EXECUTION_RUNBOOK.md) · [../07-governance-risk/RISK_REGISTER.md](../07-governance-risk/RISK_REGISTER.md)

---

## 1. Purpose and how this differs from the Risk Register

The [Risk Register](../07-governance-risk/RISK_REGISTER.md) is **forward-looking** — risks anticipated before they happen, scored and mitigated in advance. This log is **backward-looking** — a record of things that actually went wrong (or were actually discovered) while doing the work, when they were found, and how they were resolved. A risk that materializes becomes an issue here; an issue that reveals a new class of risk should be added to the Risk Register too, but the two lists are not the same list.

## 2. How to log an issue

Add a new entry at the top of Section 3 (most recent first) with the next sequential ID. Every entry needs: what happened, when, how severe, current status, and what resolved it (or what's blocking resolution). Link back to the [Execution Runbook](EXECUTION_RUNBOOK.md) task it was found during, if applicable.

## 3. Log

### ISSUE-013
**Date found:** 2026-07-15 · **Severity:** Low (self-inflicted, caught immediately) · **Status:** Fixed
**Found during:** Migrating the self-hosted runner to a dedicated `gha-runner` user ([ADR-0003](../07-governance-risk/adr/0003-dedicated-runner-user.md))
**Description:** Moved the existing runner installation from `/home/pkm/actions-runner` to `/home/gha-runner/actions-runner` via `mv` + `chown -R`, intending to preserve the warm Python/pip/npm caches. Two things broke: (1) Python's `pip` script has an absolute path baked into its shebang line at install time (`#!/home/pkm/actions-runner/.../python`); moving the directory left it pointing at a path that no longer existed, failing every job with `bad interpreter: Permission denied`. (2) `svc.sh install gha-runner` captured the *invoking* user's (`pkm`, via `sudo`) `PATH` into a `.path` file regardless of which user the service actually runs as, leaking `/home/pkm/...` paths that `gha-runner` can't read into every job's environment (`EACCES` errors on `git` and other tools).
**Resolution:** Wiped `_work` entirely (forcing a fresh Python 3.12 re-download and re-checkout under the correct new path) and manually reset `.path` to a plain system `PATH` (`/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`). Verified with a clean `workflow_dispatch` run — all jobs passed. **Lesson recorded in ADR-0003:** never `mv` an existing runner installation to change its owning user; either do a clean `config.sh`/`svc.sh install` under the target user, or immediately wipe `_work` and reset `.path` after any such move.

### ISSUE-012
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** First real CI runs on the self-hosted runner (post PR #1 merge)
**Description:** `actions/setup-python@v5`'s `cache: 'pip'` and `actions/setup-node@v4`'s `cache: 'npm'` inputs upload the pip/npm cache directory to GitHub's remote `actions/cache` service after each job. On the persistent self-hosted runner, `pip cache dir` resolves to `/home/pkm/.cache/pip` and npm's cache to `/home/pkm/.npm` — the same machine-wide caches shared by every other project on this development machine, not scoped to this repo. Those directories had grown to 4.1GB and 2.1GB respectively. A job hung indefinitely at the post-job cache-save step, stuck at "Sent 0 of 4278460165 (0.0%)" forever.
**Resolution:** Removed the `cache:`/`cache-dependency-path` inputs from all three `actions/setup-python`/`actions/setup-node` steps in `ci.yml`. This is not a workaround — it's the correct fix: pip and npm already read from those same local caches on every install regardless of `actions/cache`, and this runner's disk already persists between jobs (unlike the ephemeral GitHub-hosted runners `actions/cache` is designed for), so the remote upload/download was pure redundant overhead that happened to be actively broken here. See the explanatory comment block in `ci.yml` itself.

### ISSUE-011
**Date found:** 2026-07-14 · **Severity:** Medium · **Status:** Fixed
**Found during:** First PR-triggered CI run to actually reach the pytest step (PR #1)
**Description:** `ci.yml` invoked tests as bare `pytest backend/tests -v` / `pytest agent/tests -v`. This does not add the checkout's repo root to `sys.path`, so `from backend.app.config import ...` / `from agent.app.config import ...` failed with `ModuleNotFoundError: No module named 'backend'` (or `agent`). Never caught before because this was literally the first CI run in the repo's history to reach that step successfully — all prior verification this session used `python3 -m pytest` locally, which behaves differently (adds CWD to `sys.path[0]`) and masked the bug.
**Resolution:** Changed both invocations to `python -m pytest backend/tests -v` / `python -m pytest agent/tests -v` in `ci.yml`.

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
**Date found:** 2026-07-14 · **Severity:** Critical · **Status:** Resolved
**Found during:** Initial repository audit ([`docs/OMEGA_NEXUS_AUDIT.md`](../OMEGA_NEXUS_AUDIT.md))
**Description:** `terraform/terraform.tfstate.1774373141.backup` was committed to git and contained real, non-placeholder values for the Gemini API key and GitHub PAT (captured via `azurerm_key_vault_secret` resources in the state file). The file had already been pushed to the public `origin/main` remote.
**Resolution:** History rewritten with `git-filter-repo --path terraform/terraform.tfstate.1774373141.backup --invert-paths`; `.gitignore` fixed (ISSUE-002); force-pushed to `origin/main` with explicit user confirmation. Gemini API key and GitHub PAT subsequently rotated in their respective consoles (2026-07-14) — fully closed.

## 4. Summary by status

| Status | Count |
|---|---|
| Fixed | 11 |
| Resolved | 1 |
| Open | 1 |
