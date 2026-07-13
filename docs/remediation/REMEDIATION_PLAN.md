# OmegaNexus — Remediation Plan: Fix Critical Issues, Ready for Public Exposure

**Document Control**
* Version: 1.0 | Date: 2026-07-13 | Status: Active | Author: Portfolio Strategy / Code Audit
* Predecessor: this plan operationalizes the findings in the code-level audit summarized in [../../../../PORTFOLIO_STRATEGY.md](../../../../PORTFOLIO_STRATEGY.md) §0e. Read that section first for why this project moved from `Partial/` to `InProgress/`.
* Scope: this plan covers only the 14 items already triaged (Critical/High/Nice-to-have). It does not re-litigate whether OmegaNexus stays in the portfolio — that decision is made (§0e: yes, standalone, differentiated from BLAG).

## How to use this document

Each item has: the finding it fixes, concrete steps, files touched, a Definition of Done, and an estimate. Work phases in order — **Phase 1 (Critical) must be 100% complete before the repo is made public, linked from the portfolio site, or shown in an interview**, regardless of how far Phase 2/3 get. Do not skip ahead to RAG work while a live secret leak is still in git history.

---

## Phase 1 — Critical (must-have before showing to anyone)

### C1. Purge git history of all leaked secrets and rotate every one [COMPLETE]

**Finding:** The production internal API key (`[REDACTED_INTERNAL_KEY]`), the demo admin password (`[REDACTED_ADMIN_PASSWORD]`), and a hardcoded JWT signing key (`[REDACTED_JWT_KEY]`) are committed in plaintext across at least: `test_api.py`, `test_api.sh`, `verify_secret_fix.sh`, `backend/app/routers/health.py`, `backend/app/config.py`, `agent/app/config.py`, and 9+ of the root `*_FIX.md`/`*_STATUS.md` files. This is live in the current git history whether or not it's fixed in the latest commit.

**Steps:**
1. **Rotate first, purge second** — assume the secrets are already compromised (repo may already be on a public remote per `BUILD_DEPLOYMENT_REPORT.md`'s reference to `github.com/mittalpk/OmegaNexus`). Before touching git history:
   - Generate a new `INTERNAL_API_KEY` (32+ bytes, `secrets.token_urlsafe(32)`), rotate in Azure Key Vault.
   - Generate a new JWT `secret_key` (32+ bytes), rotate in Key Vault.
   - Change/disable the `admin`/`[REDACTED_ADMIN_PASSWORD]` demo login credential; if a demo login must exist, generate a random password and store only in Key Vault, never in code.
   - Regenerate the GitHub PAT (`github-pat` secret) and Azure Storage connection string referenced in Terraform/CI, since those also appear in incident docs.
2. **Purge history**: use `git filter-repo` (not the deprecated `filter-branch`) to strip the literal strings `[REDACTED_INTERNAL_KEY]`, `[REDACTED_ADMIN_PASSWORD]`, `[REDACTED_JWT_KEY]` from every commit, or — simpler and safer given the repo is only 103 commits over 4 days — **squash/reset to a clean history**: create a fresh orphan branch from the current tree state (after code fixes below are applied), and force-push that as the new `main`, keeping the old history only in a private, non-pushed backup. Confirm with `git log -p | grep -i <secret>` that no occurrence survives.
3. If the repo has ever been pushed to a public GitHub remote, also: check GitHub's secret-scanning alerts tab, and consider the key permanently burned (rotation in step 1 already covers this).

**Files touched:** entire git history (destructive rewrite — coordinate before running), `.env.example`, Key Vault secret values (out-of-band, via `az keyvault secret set`).

**Definition of Done:** `git log -p --all | grep -iE '[REDACTED_INTERNAL_KEY]|[REDACTED_ADMIN_PASSWORD]|[REDACTED_JWT_KEY]'` returns nothing; all three secrets rotated in Key Vault; old values no longer valid against any live endpoint (verify by curling with the old key and confirming 401).

**Estimate:** 0.5–1 day (mostly rotation + verification; history rewrite itself is fast).

---

### C2. Remove the auth bypass; implement real key comparison with fail-closed default [COMPLETE]

**Finding:** `backend/app/main.py`'s `get_current_user()` fetches `expected_key = settings.internal_api_key.get_secret_value()` but never compares it to the incoming header — any non-empty `X-Internal-API-Key` value authenticates as `{"sub": "internal-agent", "internal": True}`. Compounding this, `config.py` defaults `internal_api_key` to the literal string `"change-me-in-production"`, so a misconfigured deployment silently "succeeds" with a known-default secret instead of failing to start. The agent service's `verify_internal_key` (`agent/app/main.py`) does compare correctly — the vulnerability is backend-only, but backend is the service actually exposed to the frontend/internet.

**Steps:**
1. In `backend/app/main.py`, replace the bypass with a constant-time comparison:
   ```python
   import hmac
   ...
   if internal_key and hmac.compare_digest(internal_key, expected_key):
       return {"sub": "internal-agent", "internal": True}
   ```
2. Add a startup guard in both `backend/app/main.py` and `agent/app/main.py` (e.g. in a FastAPI `lifespan`/`startup` event) that refuses to boot if `internal_api_key` equals `"change-me-in-production"` or is empty — this was proposed in `CHANGE_SUMMARY.md` after the original incident but never implemented; implement it now:
   ```python
   if settings.internal_api_key.get_secret_value() in ("", "change-me-in-production"):
       raise RuntimeError("INTERNAL_API_KEY not configured — refusing to start")
   ```
3. Do the same fail-closed check for the JWT `secret_key` and the admin password fallback in `backend/app/config.py`.
4. Remove `skip_auth: bool = True` entirely (config.py:24) or, if real Azure AD/MSAL integration is out of scope for now (see C5 — be honest about this instead of leaving a half-wired dependency), remove `fastapi-azure-auth` from `requirements.txt` since it's imported nowhere, and keep only the JWT + internal-key model, documented as such.
5. Re-run the full auth flow manually (login → JWT → call `/api/v1/knowledge/query` → call agent `/run`) after the fix, plus a negative test (garbage `X-Internal-API-Key` value must now 401).

**Files touched:** `backend/app/main.py`, `backend/app/config.py`, `agent/app/main.py`, `agent/app/config.py`, `backend/requirements.txt`.

**Definition of Done:** A request with any non-matching `X-Internal-API-Key` value returns 401; a request with no Key Vault-configured secret (or the literal default) causes the service to fail to start, not silently serve traffic; `hmac.compare_digest` used for the comparison; covered by a new pytest case (ties into C10/H10).

**Estimate:** 0.5 day.

---

### C3. Delete or clearly label the fabricated "Simulated Fallback" data [COMPLETE]

**Finding:** `backend/app/routers/knowledge.py` (`DatabaseSubsystem.query_schemas`) hardcodes a fabricated `CREATE TABLE users (...)` fact when no real result is found and the query mentions "user"/"schema"/"database", commented `# 2. Simulated Fallback (High-Fidelity for Test 6 validation)`, and returns it to the caller labeled `"source": "Database Metadata (Live)"`. This is presenting canned data as live retrieval — the single most reputationally damaging finding in the audit, since it directly contradicts the "never fabricates, always cites" claim made about this project.

**Steps:**
1. Delete the hardcoded fallback block entirely. If a "no real source found" case needs to be handled, return an explicit empty result with `"source": "none", "note": "no matching schema found in configured sources"` — never synthesize plausible-looking data.
2. Audit `AzureWikiSubsystem`'s local-file fallback (labeled `"source": "Confluence (Simulated)"`) — this one is at least honestly labeled "Simulated," which is the right pattern; keep the label, but move it out of the default code path and make it opt-in via an explicit `DEMO_MODE=true` env var, off by default, so it can never accidentally serve in a real deployment.
3. Grep the rest of `knowledge.py` and `graph.py` for any other hardcoded/canned content (e.g. search for `# Simulated`, `# Mock`, `# Fake`, `# Demo` comments) and apply the same rule: either it's real, or it's clearly and permanently labeled as simulated and gated behind an explicit flag.
4. Update `Querydocument.md` and `Testing/PRODUCT_VALIDATION_SUMMARY.md` to remove or clearly flag "Test 6" and any other scenario that depended on fabricated data — re-validate with the fallback removed and record the honest (likely "no result found") outcome.

**Files touched:** `backend/app/routers/knowledge.py`, `Querydocument.md`, `Testing/PRODUCT_VALIDATION_SUMMARY.md`.

**Definition of Done:** No code path returns fabricated content labeled as live/real; `grep -rn "Simulated\|Mock\|Fake" backend/ agent/` shows only content that is (a) genuinely simulated, (b) clearly labeled as such in both code and API response, and (c) gated behind an explicit demo flag that defaults off.

**Estimate:** 0.5 day.

---

### C4. Remove unauthenticated debug endpoints [COMPLETE]

**Finding:** `backend/app/main.py`'s `/debug/config` and `backend/app/routers/auth.py`'s `/debug` return secret lengths/prefixes and whether they equal known hardcoded strings, registered outside any auth dependency. `backend/app/routers/health.py` goes further and hardcodes the literal production key (`api_key == "[REDACTED_INTERNAL_KEY]"`) directly in an unauthenticated route, per its own docstring "no auth required."

**Steps:**
1. Delete `/debug/config` and `/debug` entirely — these were diagnostic scaffolding for the 401 incident and have no reason to exist post-fix.
2. In `backend/app/routers/health.py`, remove the hardcoded secret-value comparison; a health check should return liveness/readiness (e.g. "can this service reach the agent service," "is the Key Vault-sourced config present and non-default") without ever echoing or comparing against a literal secret value in source.
3. If a config-sanity check is still wanted operationally, gate it behind the same auth dependency as every other route (`Depends(get_current_user)`), and return only booleans ("configured": true/false), never lengths, prefixes, or literal comparisons.

**Files touched:** `backend/app/main.py`, `backend/app/routers/auth.py`, `backend/app/routers/health.py`.

**Definition of Done:** No unauthenticated route returns any information derived from a secret value (length, prefix, equality check); `curl` against `/debug/config`, `/auth/debug` returns 404.

**Estimate:** 0.25 day.

---

### C5. Rewrite README/ARCHITECTURE to describe only what's actually implemented [COMPLETE]

**Finding:** README.md and ARCHITECTURE.md claim Gemini 1.5 Pro (actual: 2.5 Flash/Pro), Azure Entra ID OAuth zero-trust (actual: JWT + shared-secret header, `skip_auth=True`), iterative multi-hop agentic loops (actual: fixed single-pass pipeline, `evaluate` node is a no-op), vector-based RAG (actual: keyword/substring search), and an Nginx reverse proxy for `/api/*` (actual: `nginx.conf` has no such block). This doc/code mismatch is, on its own, disqualifying to a technical reviewer who reads the code — it reads as either not understanding the system or misrepresenting it.

**Steps:**
1. Rewrite README.md's architecture summary to match reality post-fix: name the actual models used, describe the pipeline honestly as "single-pass plan → execute → respond" (or as a real loop, if H9 below is implemented first — sequence this after H9, see Phase ordering note), describe retrieval as "keyword/full-text search over GitHub code search + Azure Blob text, no vector index" (or "vector search over X" once H6 lands), and describe auth as what C2 actually implements.
2. Rewrite ARCHITECTURE.md's diagram/prose to remove the VNet/NSG "zero-trust network isolation" claim unless AR-follow-up H11 actually wires Container Apps into that VNet (currently they deploy into an external, shared Container App Environment from a different project — either fix the Terraform to actually use the declared VNet, or remove the VNet/NSG resources and the claim together).
3. Add a short, explicit "Known Limitations" section to README.md — this is a portfolio strength, not a weakness, when done deliberately (the frontend's own FAQ tab already does this candidly for RAG; extend the same honesty to auth, evaluation, and observability until those are built).
4. Treat every remaining `*_FIX.md`/`*_STATUS.md`/`*_COMPLETE.md` root file as a historical record, not living documentation: move all 14 into a `docs/incident-history/` subfolder with a one-line index, so they read as "here is my incident-response process" (a genuine asset) rather than being mistaken for current-state documentation.

**Files touched:** `README.md`, `ARCHITECTURE.md`, all 14 root `*_FIX.md`/`*_STATUS.md`/`*_COMPLETE.md` files (relocate), `terraform/main.tf` (if VNet claim is fixed rather than removed).

**Definition of Done:** Every capability claim in README.md/ARCHITECTURE.md is verifiable by reading the corresponding code; a fresh reader (or the next audit) finds zero doc/code contradictions; incident docs are clearly archival.

**Estimate:** 1 day (more if sequenced after Phase 2 items it depends on — see ordering note below).

**Ordering note:** C5 should be done twice, not once: a first pass now (to make the repo honest immediately, unblocking "safe to show" status), and a final pass after Phase 2's H6/H9 land (to describe the improved architecture accurately). Don't let "wait for the real RAG build" block Phase 1 sign-off — ship the honest-but-modest description now.

---

### Phase 1 exit criteria

All five items above complete, verified by: (a) a fresh `git log -p --all | grep` for the three rotated secrets returns nothing, (b) a negative-auth curl test 401s, (c) no fabricated data returned by any endpoint, (d) no unauthenticated route reveals secret-derived info, (e) README/ARCHITECTURE pass a re-read against the code with zero contradictions found. **Only after this checklist passes should the repo be pushed to a public remote, linked from the portfolio site, or referenced in an application/interview.**

---

## Phase 2 — High Priority (needed to credibly claim "Senior AI Engineer")

### H6. Implement actual RAG (real chunking + embeddings + vector search)

**Finding:** `knowledge.py`'s `AzureWikiSubsystem`/`GitHubSearchSubsystem` do plain substring/keyword matching — no embeddings, no chunking, no ranking. The frontend's own FAQ tab already admits this gap.

**Steps:**
1. Pick one vector store appropriate to the existing Azure footprint to avoid adding a new cloud dependency: **pgvector on Azure Database for PostgreSQL** (fits the existing Azure Container Apps/Key Vault setup better than standing up a new Chroma/Pinecone service) or **Azure AI Search** (native vector index, already in the same cloud, no new infra to manage). Recommend Azure AI Search given it's a named skill line in `TragetedSkills.md`/`PORTFOLIO_STRATEGY.md`'s Azure/AI Foundry gap.
2. Build an ingestion pipeline: pull the same sources (GitHub repos, Azure Blob wiki docs) → chunk (e.g. 512-token windows with overlap) → embed (Gemini embeddings, consistent with the existing Gemini usage, or `text-embedding-3-small` if staying provider-agnostic) → upsert into the vector index with source metadata (repo, path, commit SHA / blob URL) preserved for citation.
3. Replace `GitHubSearchSubsystem`/`AzureWikiSubsystem`'s substring matching with a vector similarity query (top-k, e.g. k=5) plus a lightweight keyword pre-filter (repo/path) for precision — hybrid search, not pure vector, is the right pattern for code+doc retrieval and is worth stating explicitly as a design decision.
4. Keep `DatabaseSubsystem` as keyword-based schema search (schemas are typically small and structured; vectorizing DDL doesn't add much) but document this as a deliberate choice, not an oversight.
5. Re-run `Querydocument.md`'s scenarios against the new pipeline and update `Testing/` with real before/after retrieval quality (ties into H7).

**Files touched:** new `backend/app/rag/` module (ingestion, embedding, retrieval), `backend/app/routers/knowledge.py`, `backend/requirements.txt` (vector client SDK), Terraform (Azure AI Search resource or pgvector-enabled Postgres), `.env.example`.

**Definition of Done:** `/api/v1/knowledge/query` results come from vector similarity search with citations back to source location; a documented ingestion script/job exists and can be re-run; retrieval quality is measured, not asserted (see H7).

**Estimate:** 3–5 days.

---

### H7. Build a real evaluation harness

**Finding:** "Validation" is currently a human running `Querydocument.md`'s scenarios once and self-grading `Testing/PRODUCT_VALIDATION_SUMMARY.md` as 14/14 PASS. No RAGAS, no golden dataset, no automated scoring.

**Steps:**
1. Turn `Querydocument.md`'s ~14 scenarios into a structured golden set: `evals/golden_qa.jsonl`, each row `{query, expected_facts: [...], expected_sources: [...], category}`.
2. Add 10–15 more cases covering negative scenarios (no answer should exist — verifies C3's fix holds), ambiguous queries, and multi-hop queries that need 2+ sources combined.
3. Implement an eval script (`scripts/run_eval.py`) using RAGAS (faithfulness, answer relevance, context precision/recall) or a simple LLM-as-judge rubric if RAGAS's dependency footprint is too heavy for this project's scope — either is acceptable, but it must be automated and produce a numeric score, not a hand-written PASS/FAIL narrative.
4. Store eval results with a timestamp/commit SHA so score trends over time are visible (`evals/results/`), and surface a summary table in README.md.
5. Cross-reference `PORTFOLIO_STRATEGY.md`'s RAGEVAL project (`Backlog/RAGEVAL/SRS.md`) — if RAGEVAL's shared evaluation platform exists by the time this is built, OmegaNexus should be its first/second consumer via the planned `RAGTarget` adapter interface rather than building a fully bespoke harness; if RAGEVAL isn't built yet, build OmegaNexus's harness standalone now and port it later.

**Files touched:** new `evals/` directory, `scripts/run_eval.py`, `requirements.txt` (ragas or equivalent), README.md (results summary), `.github/workflows/deploy.yml` (optional: run eval as an informational CI step, not yet a hard gate until H10's test infra exists).

**Definition of Done:** Running `python scripts/run_eval.py` produces a numeric faithfulness/relevance/precision score against a versioned golden set of 20+ cases, including negative cases; no more self-graded narrative "validation" documents are treated as evidence of correctness.

**Estimate:** 2–3 days.

---

### H8. Add tracing/observability (LangSmith or OpenTelemetry)

**Finding:** No tracing exists anywhere — only plain `logging` calls, some of which log secret-derived metadata (a minor info-leak pattern flagged separately, fix alongside C4).

**Steps:**
1. Instrument `agent/app/graph.py` with LangSmith tracing (simplest given LangChain/LangGraph is already the framework in use — set `LANGCHAIN_TRACING_V2=true` + API key, near-zero code change) or OpenTelemetry spans around each graph node (`plan`, `execute`, `respond`) plus the outbound HTTP calls to backend tools if a vendor-neutral approach is preferred for the portfolio narrative.
2. Propagate a request/trace ID from the frontend → backend → agent, and surface it in the frontend's existing "execution-trace timeline" UI (App.tsx already renders a trace view for the multi-agent tab — wire it to the real trace ID instead of just the locally-assembled step list, if feasible without major frontend rework).
3. Ensure no logged span/attribute ever includes a secret value, length, or prefix (audit alongside C4).
4. Document in README.md how to view a trace (LangSmith project link or OTel collector/Jaeger setup).

**Files touched:** `agent/app/graph.py`, `agent/app/main.py`, `backend/app/main.py`, `requirements.txt` (langsmith or opentelemetry packages), `docker-compose.yml` (if adding a local OTel collector/Jaeger for local dev).

**Definition of Done:** Every `/run` and `/api/v1/knowledge/query` call produces a retrievable trace showing each step's latency and inputs/outputs (with secrets redacted); README documents how to view one.

**Estimate:** 1–2 days.

---

### H9. Make the LangGraph loop real, or stop claiming it's iterative

**Finding:** `should_continue()` (`graph.py`) always returns `"respond"`; `node_evaluate` is `return {}`. The graph API is used, but not its cyclic capability — this is the clearest gap between "used LangGraph" and "used LangGraph's actual differentiator" for a portfolio meant to demonstrate agent orchestration.

**Steps (pick one, don't leave it ambiguous):**
- **Option A — make it real:** implement `node_evaluate` to actually assess whether retrieved evidence is sufficient to answer the query (e.g., an LLM call with a structured output schema `{"sufficient": bool, "missing": [...], "next_tool": str | null}`), and have `should_continue()` route back to `execute` (bounded to e.g. 3 iterations to prevent runaway loops/cost) when insufficient, or to `respond` when sufficient or iteration budget exhausted. This is the stronger portfolio signal and should be done if H6 (real RAG) is also being built, since "insufficient evidence" only means something once retrieval quality varies meaningfully.
- **Option B — be honest instead:** if iterative refinement isn't going to be built, simplify the graph to a linear `plan → execute → respond` chain (remove the unused conditional edge and the no-op `evaluate` node), and remove every claim of "iterative," "loops," or "conditional edges" from README/ARCHITECTURE (feeds into C5's second pass).

**Recommendation:** Option A, sequenced after H6 — a real iterative loop over a real vector-search retrieval step is a materially stronger interview story ("the agent re-queries when the first pass under-retrieves, bounded by a 3-iteration budget and a cost ceiling") than either the current fake loop or a deliberately-simplified linear pipeline.

**Files touched:** `agent/app/graph.py`, README.md/ARCHITECTURE.md (second pass).

**Definition of Done:** Either the graph demonstrably loops (add a test case where the first retrieval is deliberately insufficient and verify a second `execute` pass occurs, bounded by an iteration cap), or all iterative/looping language is removed from every doc.

**Estimate:** 1–2 days (Option A) / 0.25 day (Option B).

---

### H10. Add a pytest suite with CI test/lint gates before deploy

**Finding:** Zero automated tests anywhere. `test_api.py`/`test_api.sh`/`verify_secret_fix.sh` are manual curl-style scripts against the live production URL (and, per C1, hardcode secrets). `deploy.yml` has no test or lint job.

**Steps:**
1. Delete or fully rewrite `test_api.py`/`test_api.sh`/`verify_secret_fix.sh` — replace with real `pytest` tests using `httpx.AsyncClient`/FastAPI's `TestClient` against the app in-process (no live URL, no live secrets required).
2. Minimum coverage for Phase 1 sign-off: auth (valid JWT succeeds, invalid/missing 401s, C2's fixed internal-key comparison — both a correct-key-succeeds and a wrong-key-fails case), knowledge query (happy path returns expected shape, no-result case returns the honest empty response from C3, not fabricated data), health check (no longer leaks secret comparisons per C4).
3. Add `pytest`, `ruff` (or `flake8`), and `mypy` (optional but a strong signal) as a required job in `.github/workflows/deploy.yml`, gating the existing build/push/deploy jobs — a failing test or lint check must block deployment.
4. Add `npm test`/`eslint` for the frontend (even a minimal smoke test — the app renders, login form submits) as a parallel required CI job.

**Files touched:** new `backend/tests/`, `agent/tests/`, `frontend/src/**/*.test.tsx`, `.github/workflows/deploy.yml`, delete `test_api.py`/`test_api.sh`/`verify_secret_fix.sh`.

**Definition of Done:** `pytest` passes locally and in CI with real assertions (not smoke prints); `deploy.yml` has a `test` job that must succeed before any `deploy-*` job runs; no script in the repo embeds a live secret or calls a live production URL.

**Estimate:** 2–3 days.

---

### H11. Fix CORS to explicit allowed origins; fix Terraform/CI ownership split

**Finding:** Both services use `allow_origins=["*"]` + `allow_credentials=True` (invalid combination per CORS spec, evidence of trial-and-error debugging). Separately, Terraform hardcodes all three Container Apps to `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest` with `lifecycle { ignore_changes = [image] }`, while CI does the real image deploys via raw `az containerapp update` — two disconnected sources of truth for the same resources, the root cause of the original secret-injection incident chain. Also: Container Apps are deployed into a shared, externally-referenced Container App Environment from a different project (`nexvocab-env-prod`), not into the VNet/NSG this repo defines, so the "zero-trust network isolation" claim is moot regardless of C5's doc fix.

**Steps:**
1. Replace `allow_origins=["*"]` with an explicit list from config (`ALLOWED_ORIGINS` env var, e.g. the frontend's actual Container App FQDN + `localhost` for dev) in both `backend/app/main.py` and `agent/app/main.py`.
2. Pick one Terraform/CI ownership model and make it explicit rather than accidental:
   - **Preferred:** have Terraform manage the real image tag too (`image = "ghcr.io/.../backend:${var.image_tag}"`, passed as a `-var` from CI after build/push), remove the `ignore_changes` lifecycle block, and have CI run `terraform apply` instead of raw `az containerapp update` calls. This makes Terraform the actual source of truth and closes the drift gap that caused the original incident.
   - **Acceptable alternative:** keep CI as the sole owner of image deploys, but document this explicitly in ARCHITECTURE.md/README.md ("Terraform provisions infrastructure once; GitHub Actions owns image rollouts; do not run `terraform apply` for image changes") so the split is a documented decision, not a discovered inconsistency.
3. Provision (or reference) a dedicated Container App Environment for this project instead of the shared `nexvocab-env-prod`, and either wire it into the VNet/NSG already defined in `main.tf`, or remove the unused VNet/subnet/NSG resources if network isolation isn't actually being pursued (don't leave dead IaC that implies a security boundary that doesn't exist).
4. Move the hardcoded subscription ID / Key Vault name out of `deploy.yml` into repository/organization-level GitHub secrets or Terraform outputs consumed via `terraform output`, so they're not committed in plaintext in a workflow file (lower severity than C1's secrets, but same category of issue).
5. Fix the internal service-to-service URL inconsistency (`agent`'s `BACKEND_URL` uses the external HTTPS FQDN while `terraform/main.tf` defines an internal DNS name) — use the internal Container Apps DNS name consistently for service-to-service calls, reserving external FQDNs for the frontend-facing route only.

**Files touched:** `backend/app/main.py`, `agent/app/main.py`, `backend/app/config.py`, `agent/app/config.py`, `terraform/main.tf`, `terraform/variables.tf`, `.github/workflows/deploy.yml`.

**Definition of Done:** CORS only accepts a configured allowlist; a `terraform plan` after a CI deploy shows no unexpected diff (or the CI-owns-images split is explicitly documented as intentional); no dead VNet/NSG resources remain unless actually applied to the deployed Container Apps; no subscription ID/Key Vault name literals in `deploy.yml`.

**Estimate:** 2–3 days (more if pursuing the "Terraform owns images" option, which also touches remote state — see N12).

---

## Phase 3 — Nice-to-have

### N12. Modularize Terraform, add dev/prod workspaces, move state to a remote backend

**Finding:** Single flat `main.tf` (465 lines), no `modules/`, no per-environment `.tfvars`/workspaces, local `.tfstate`/backup files left in the working tree instead of a remote backend (Azure Storage), `fix_state.sh`/`import_secrets.sh` ad hoc scripts confirming manual state management.

**Steps:** Extract `modules/container-app/`, `modules/key-vault/`, `modules/networking/`; add `environments/dev.tfvars`/`environments/prod.tfvars`; configure an `azurerm` remote backend (Storage Account + container, with state locking via blob lease); delete committed `.tfstate*` files from the working tree and `.gitignore` them; retire `fix_state.sh`/`import_secrets.sh` once the backend is stable (or keep them as documented one-time migration scripts, clearly labeled, not part of routine operation).

**Estimate:** 2–3 days.

### N13. Add rate limiting, non-root Docker users, container image scanning

**Steps:** Add `slowapi` (or Azure API Management / Container Apps-level rate limiting) to both FastAPI services; add `USER appuser` (non-root) to all three Dockerfiles' final stage; add `HEALTHCHECK` directives; add Trivy or `docker scout` as a CI step scanning built images before push, failing the build on critical/high CVEs.

**Estimate:** 1 day.

### N14. Remove unused `axios` dependency; clean up leftover debug artifacts

**Steps:** Remove `axios` from `frontend/package.json` (unused — `client.ts` uses raw `fetch`); remove the `console.log('🚀 Omega Nexus Production UI loaded...')` debug line from `App.tsx`; remove deploy-trigger comments (`# Triggering full rebuild...`, `# Deployment Trigger: ...`) from `agent/app/main.py`/`backend/app/main.py` — use empty commits or workflow `workflow_dispatch` for manual redeploy triggers instead of source edits.

**Estimate:** 0.25 day.

---

## Sequencing summary

| Phase | Items | Gate |
|---|---|---|
| **1 — Critical** | C1–C5 | Must complete before repo is public, linked, or shown in an interview. Est. 3 days. |
| **2 — High** | H6–H11 (H9 sequenced after H6; C5's second pass sequenced after H6/H9) | Needed before claiming "production-grade RAG/agent system" in interviews. Est. 12–19 days. |
| **3 — Nice-to-have** | N12–N14 | Polish; do opportunistically, don't block Phase 2 completion on these. Est. 3–4 days. |

Total estimated effort: **~3 days (Critical) + ~2.5–4 weeks (High) + ~3–4 days (Nice-to-have)**, roughly 4–5 weeks of focused part-time work to take OmegaNexus from its current state to a genuinely defensible Senior AI Engineer / AI Solutions Architect portfolio piece — consistent with the "finish, don't rebuild" framing in [PORTFOLIO_STRATEGY.md](../../../../PORTFOLIO_STRATEGY.md) §0b, but only once Phase 1 is done first.

## Exit back to the portfolio

Once Phase 1 is complete, move this project from `InProgress/` back to `Partial/` (or directly to a new top-level "standalone" location matching the other finished flagships, per `PORTFOLIO_STRATEGY.md` §1's target structure) and update `index.md`/`PORTFOLIO_STRATEGY.md` §0e accordingly. Once Phase 2 is complete, update the original AR4 assessment table to reflect the real (now accurate) capabilities, and consider this project ready to link from the public portfolio site.
