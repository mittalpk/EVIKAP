# Omega Nexus — Architecture & AI Engineering Audit

**Independent technical audit — 2026-07-14**
Scope: architecture, AI engineering, production readiness, team capability signal
Perspective: Senior AI Solutions Architect / AI SME / Forward Deployed Engineer review

> Omega Nexus has real engineering discipline — a genuine trust boundary between agent and data, fail-closed secret handling, a documented remediation history. But the parts that would prove AI-engineering seniority — retrieval, iteration, evaluation, observability — are either absent or simulated. This report scores the gap and prices out what closing it would take.

**Snapshot:** 65 tracked files · ~2,585 LOC · FastAPI + LangGraph + Gemini · Azure Container Apps · 5-commit curated history

| Dimension | Score |
|---|---|
| Technical depth | 4/10 |
| Engineering maturity | 5/10 |
| Business value shown | 4/10 |
| Innovation | 3/10 |
| **Overall audit score** | **4.2/10** |
| **Seniority currently demonstrated** | Mid-level cloud engineering |

---

## 1. Architecture Review

A defensible three-service split undercut by a data layer that exists only in documentation.

### What's actually well-designed

The trust-boundary model is real, not aspirational. The agent service (`agent/`) carries no GitHub or Azure SDK imports at all — it can only reach data through the backend's `/api/v1/knowledge/query` endpoint, and Terraform sets `ingress.external_enabled = false` on the agent's Container App so it isn't even network-reachable from outside. That's a genuine security-by-architecture decision, correctly enforced in both code and infrastructure, and it's the single strongest engineering signal in the repo.

The service boundaries also map cleanly to failure domains: frontend (static, stateless), backend (the only service holding data-source credentials), agent (reasoning only, no credentials). Startup guards in both services fail closed — refusing to boot on default, empty, *or SHA-256-hash-matched-to-a-known-leaked-value* secrets — which is an unusually mature detail for an early-stage codebase and points to a prior incident that was taken seriously.

### Where it breaks down

The README markets a "4-layer cloud-native system" with SQL databases as a first-class Layer-1 source. There is no database client, no ORM, no migration, and `sqlalchemy`/`asyncpg` aren't even dependencies. `DatabaseSubsystem.query_schemas()` doesn't query a database — it searches GitHub for filenames containing `.sql` or the word "schema." The architecture diagram describes a capability that was never built; this is the kind of gap a Forward Deployed Engineer interview will find in the first five minutes of a live demo.

Infrastructure has a second, quieter version of the same problem: the VNet and NSGs in `terraform/main.tf` are provisioned but the Container Apps actually deploy into a *pre-existing, external environment* (`nexvocab-env-prod` — borrowed from a different project) that the new network resources never touch. The architecture doc self-discloses this as "planned/partial," which is honest, but it means the network-isolation story in the README is not the network-isolation story running in production.

Terraform also never manages the real container image — `ignore_changes` is set on every `template.container.image` field, with CI/CD pushing images out-of-band via `az containerapp update`. This is a workable pattern but it means Terraform's state and the actual running system permanently diverge, and the presence of manual drift-repair scripts (`fix_state.sh`, `import_secrets.sh`) in the repo suggests that divergence has already caused real pain once.

**Read this as:** a team that got the hard security call right (trust boundaries, fail-closed secrets) and the unglamorous plumbing wrong (data layer, IaC/runtime drift). That pattern — strong judgment on the parts that get discussed in design reviews, weak follow-through on the parts that only show up under load — is exactly what a Staff-level review is trained to catch.

---

## 2. Feature Assessment

The feature list is honest about intent, dishonest about delivery — three of the four headline capabilities are simulated.

| Claimed capability | What's actually implemented | Gap |
|---|---|---|
| Unified semantic retrieval | Keyword/substring matching over GitHub file trees and downloaded blob content | **Critical** |
| Multi-agent reasoning engine | Single LangGraph node graph, one agent, one non-branching pass | **Critical** |
| Stateful, iterative agent loop | `should_continue()` unconditionally returns `respond`; `node_evaluate` is an empty stub | **Critical** |
| SQL database source | GitHub filename search for files that look database-related | **Critical** |
| Confluence wiki integration | Local file fallback, gated behind a `DEMO_MODE` flag | Partial |
| JWT + service-key auth | Actually implemented, constant-time comparison on the service key | Delivered |
| Secrets via Key Vault + managed identity | Actually implemented and wired into CI/CD | Delivered |
| Health probes | Real endpoints, wired into Container App liveness/readiness | Delivered |

The `max_iterations` parameter is accepted on both the backend and agent request models and threaded all the way through the API contract — but it's never read anywhere inside `graph.py`. This is worse than not having the feature: a caller who sets `max_iterations: 5` expecting bounded refinement gets exactly the same single-pass answer as a caller who sets `1`. Anyone who asks "walk me through what happens when the agent doesn't find enough evidence on the first pass" will find there's no answer, because that path was never built — only its parameter.

What's missing entirely from a "production-grade AI solution" checklist: no evaluation harness, no observability, no guardrails, no model fallback, no multi-tenancy, no RBAC, no caching beyond an unbounded process-local dict. These aren't polish items — they're the categories any serious AI Solutions Architect / AI SME review will ask about by name.

---

## 3. AI Engineering Evaluation

The LLM call itself is competently wired. Everything an AI engineering org builds around that call is missing.

### LLM integration

Model choice is sensible and cost-aware in intent: `gemini-2.5-flash` for planning, `gemini-2.5-pro` for final synthesis, via `langchain-google-genai`. Tool binding uses LangChain's standard `bind_tools()` pattern. But `backend/app/config.py` also declares `openai_api_key`, `azure_openai_endpoint`, and `azure_openai_deployment` fields that nothing reads, and the Azure deployment doc references an `OPENAI_API_KEY` for a service that has no OpenAI SDK import anywhere. Dead configuration that contradicts the actual provider is a small thing individually, but it's the kind of inconsistency that erodes confidence fast in a live walkthrough.

### RAG — the core gap

> **No retrieval-augmented generation exists in this repository.** There is no vector database, no embedding model, no chunking strategy, no reranking, and no hybrid search. "Semantic retrieval" in the README refers to `extract_keywords()` — stopword filtering plus regex tokenization — feeding either the GitHub Search API or a substring scan of full-text blob downloads. For every wiki query, every `.md` blob in the container is downloaded and scanned in full; there is no index. This is table-stakes 2023 functionality being described in aspirational 2026 marketing language as a "unified semantic retrieval layer."

### Agent orchestration

LangGraph is used as a state-machine skeleton (`plan → execute → evaluate → respond`) but the `evaluate` node does nothing and the conditional edge is unconditional. What's marketed as "stateful, iterative reasoning that continues until sufficient evidence is gathered" is, in the running code, a single plan → parallel-tool-execute → synthesize pass — indistinguishable from a plain function-calling loop with extra ceremony. This matters specifically at the competency level this document is assessed against: a Forward Deployed Engineer is expected to build the iterative, self-correcting agent behavior that's missing here, and an AI SME is expected to know the difference between a state graph and a state graph that's actually stateful.

### Evaluation, observability, guardrails, model management

- **Evaluation:** none automated. `PRODUCT_VALIDATION_SUMMARY.md` (originally `docs/testing/`, since moved to the untracked, local-only `.doc/testing/` archive as a superseded artifact) is a hand-written narrative of 14 manually-run scenarios, not a golden-dataset regression suite. No RAGAS, no LLM-as-judge, no CI-gated quality check.
- **Observability:** stdlib `logging` only. Application Insights / OpenTelemetry is described in the Azure deployment doc's "Phase 8" but zero `opentelemetry-*` packages exist in either service's dependencies — pure aspirational documentation. No trace IDs, no per-call token/cost/latency capture, no LangSmith/Langfuse.
- **Guardrails:** a single prompt instruction ("focus on facts found"). No prompt-injection defense, no output schema validation, no PII redaction, no toxicity/jailbreak filtering.
- **Model management:** two hardcoded models, no fallback provider, no adaptive routing by task complexity or cost, no prompt versioning/registry.

| Sub-dimension | Score |
|---|---|
| RAG maturity | 1/10 |
| Agent orchestration | 3/10 |
| Evaluation & observability | 1/10 |
| Guardrails & safety | 1.5/10 |

---

## 4. Production Readiness

Genuine security instincts on secrets, undermined by gaps that would block enterprise sign-off.

Two authentication paths coexist: a shared-secret header for service-to-service calls (correctly compared with `hmac.compare_digest`), and a JWT issued from a single hardcoded admin username/password compared with plain `!=` — not constant-time, unlike its sibling check a few files away. There is no user table, no RBAC, no scopes: every authenticated caller has identical access to every router. `skip_auth: bool = True` sits in `config.py` with a comment flagging it as a "temporary bypass" — it's actually dead code that nothing reads, but it reads as a live landmine to anyone scanning the config, which is its own kind of code-hygiene risk.

CI/CD builds and deploys to production containers on every push to `main` with **no test step in the pipeline** — the pytest suites that exist (and are genuinely good, see below) never run before a deploy. There's no rate limiting anywhere, so both the login endpoint and the (expensive, unbounded-outbound-call) knowledge-query endpoint are exposed to abuse. The query cache is an unbounded, per-process, non-evicting dict — a memory-leak shape that also fails to do its job under Container Apps' horizontal scale-out, since it isn't shared across replicas.

> **Resolved during this review:** A Terraform state backup (`terraform.tfstate.1774373141.backup`) was committed to git with real Gemini API key and GitHub PAT values, because the `.gitignore` pattern `*.tfstate.backup` didn't match the timestamped filename. The file had already been pushed to the public GitHub remote. History was rewritten with `git-filter-repo`, the `.gitignore` pattern was broadened, and the branch was force-pushed. **The exposed API key and GitHub PAT still need to be rotated** — a history rewrite does not undo exposure that already happened.

### What's genuinely solid

- Fail-closed startup guards that block known-compromised secret hashes, not just weak defaults — evidence of a prior incident taken seriously.
- A real backend test suite (`backend/tests/test_backend.py`) with a regression test proving a previously-fabricated database-schema fallback was removed — rare to see a codebase at this stage test for "the AI doesn't make things up" as an explicit case.
- Key Vault + managed identity for secrets, correctly wired through CI/CD.

### What blocks enterprise adoption today

- No RBAC / multi-tenancy — a single shared admin identity cannot back an enterprise deployment.
- No CI test gate — nothing prevents a regression from reaching production.
- Zero frontend test coverage.
- No rate limiting or WAF-equivalent in front of public endpoints.
- No real observability — an incident today would be debugged by reading raw stdout logs.

---

## 5. Team Capability & Engineering Maturity Assessment

Strong enough to open a conversation about cloud/security engineering competency. Not yet strong enough to close one about AI engineering seniority.

At a **Senior AI Solutions Architect** or **AI SME** level of competency, this codebase should evidence RAG design decisions (chunking strategy, embedding model choice, hybrid retrieval, reranking), agent evaluation methodology, and cost/latency tradeoffs under real traffic. None of that surface area exists here to discuss — the honest answer to "walk me through the retrieval strategy" is "there isn't one; it's keyword substring matching branded as semantic search."

At a **Forward Deployed Engineer** level of competency, the bar is: can this go into a client's messy environment and stand up something that actually works end-to-end under real constraints. The trust-boundary design and the documented remediation history are genuinely strong signals of that judgment under real security pressure. But it needs to survive a live demo against a skeptical technical stakeholder, and the single-pass "multi-agent" graph and fictional database layer would not survive that demo today.

At an **AI Platform Engineer** or **Staff AI Engineer** level of competency, the missing pieces — evaluation harness, observability, model routing, guardrails — are not nice-to-haves, they're the core of the job. Their absence is the most direct evidence against the "production ready" claim in the project's own validation summary.

| Dimension | Score | Why |
|---|---|---|
| Technical depth | 4/10 | Real infra/security depth; AI depth is largely absent (no RAG, no real agent loop, no evals) |
| Engineering maturity | 5/10 | Fail-closed guards and a documented remediation pass show real discipline; undermined by no CI test gate and IaC/runtime drift |
| Business value demonstrated | 4/10 | Compelling narrative ("unify scattered enterprise knowledge") but the core value driver — retrieval quality — isn't substantiated by working retrieval |
| Innovation | 3/10 | Branded as multi-agent/iterative; implementation is a single-pass tool-calling loop |

---

## 6. Enhancement Recommendations

Prioritized by what closes the AI-engineering credibility gap fastest.

### High priority — must-have (closes the "this isn't actually AI engineering" gap)

- **Real RAG pipeline** — embeddings (e.g. `text-embedding-004`), a vector store (pgvector/Qdrant), chunking with overlap, and hybrid (keyword + vector) retrieval with reranking. This single change replaces the weakest part of the current story with the strongest.
- **Genuine iterative agent loop** — implement `node_evaluate` for real, make `should_continue` branch on evidence sufficiency, and actually enforce `max_iterations`. Without this, "multi-agent reasoning engine" is a label, not a behavior.
- **Evaluation harness** — a golden query/answer dataset, automated scoring (RAGAS faithfulness/relevancy or an LLM-as-judge rubric), run in CI on every change to prompts or retrieval logic. This is the artifact that proves "I know how to ship LLM changes safely," which is the core AI SME competency.
- **LLM observability** — Langfuse or OpenTelemetry GenAI semantic conventions, capturing per-call token cost, latency, and trace-level tool sequences. Turns "trust me it works" into a dashboard.
- **CI test gate before deploy** — the existing pytest suites are good; they just need to actually block a bad deploy.

### Medium priority — should-have (rounds out production credibility)

- **Real database layer** — a Postgres instance with an actual schema and migrations, so the "SQL Databases" data source is a working integration, not a filename search.
- **RBAC + multi-user auth** — replace the single hardcoded admin with real user records, roles, and scoped access to sources/tools.
- **Guardrails** — prompt-injection detection on retrieved content before it reaches the LLM, output schema validation, basic PII redaction on responses.
- **Model routing/fallback** — a second provider (or open-weight model via an inference endpoint) as a cost/availability fallback, chosen adaptively by query complexity.
- **Fix the Terraform/runtime drift** — wire the VNet/NSG to the actual Container Apps, or remove them and document the real network posture honestly.

### Nice-to-have — differentiators (separate "solid" from "flagship")

- **Knowledge graph layer** (Neo4j) for relationship-aware retrieval across code/docs/wiki — a strong differentiator against every candidate who only built vector RAG.
- **MCP server** exposing the Knowledge API as a standard Model Context Protocol tool, so any MCP-compatible agent (Claude, others) can consume it — directly relevant to how the industry is standardizing tool access in 2026.
- **Human-in-the-loop approval** for any agent action with side effects, with a review queue UI.
- **Multi-tenancy** with per-tenant data isolation and usage metering.

---

## 7. Enterprise-Level Improvements

The specific additions that read as "this person has shipped inside a large org," mapped against what exists today.

| Capability | Current state | What it demonstrates once added |
|---|---|---|
| Multi-agent architecture | Not present — single agent, single pass | Specialist sub-agents (code, docs, data) behind an orchestrator with real delegation and result synthesis |
| MCP integration | Not present | Standards-based tool exposure — increasingly expected knowledge in 2026 AI platform roles |
| Advanced RAG | Not present — keyword substring only | Chunking, hybrid search, reranking, query rewriting |
| Knowledge graph integration | Not present | Relationship-aware retrieval beyond flat document similarity |
| Human-in-the-loop workflows | Not present | Safe handling of any future write/action capability |
| Evaluation & benchmarking | Manual narrative only | Repeatable, CI-gated quality assurance for LLM behavior |
| LLM observability | Not present | Debuggability and cost accountability at scale |
| Security & governance | Partial — good secret hygiene, no RBAC/audit log | Enterprise-grade access control and traceability |
| Multi-tenancy | Not present | The difference between a demo and a sellable platform |
| Kubernetes deployment | Not present — Container Apps only | Portability and the orchestration depth many enterprises require |
| Infrastructure as Code (Terraform) | Present but drifted | Fixing the drift demonstrates IaC discipline, not just IaC syntax |
| CI/CD pipelines | Present, untested | A pipeline that actually gates on quality, not just builds/ships |
| Cost optimization | Not present | Token/infra cost tracking and routing decisions grounded in cost data |
| Caching strategy | Naive, unbounded, per-process | A distributed cache (Redis) with real eviction and hit-rate metrics |
| Model routing | Not present — hardcoded two-tier | Adaptive, cost/latency-aware provider selection |
| Feature flags | Not present | Safe progressive rollout of agent/prompt changes |
| API versioning | Present — `/api/v1/` prefix used consistently | Already a positive signal; extend with a deprecation policy |
| Event-driven architecture | Not present — synchronous request/response only | Async ingestion pipelines (Kafka/Service Bus) for source indexing at scale |

---

## 8. Maturity Roadmap

Three phases, ordered so each one is independently demonstrable and the credibility gap closes fastest, not last.

### Phase 1 — Foundation Hardening (~2–4 weeks)

- Rotate exposed Gemini key and GitHub PAT; confirm history purge propagated
- Real Postgres database with actual schema + migrations
- CI test gate blocking deploy on failure
- RBAC replacing the single hardcoded admin
- Rate limiting on public endpoints
- Frontend test suite (Vitest + RTL)
- Fix Terraform/Container-App network drift

### Phase 2 — Real AI Engineering (~4–8 weeks)

- Embeddings + vector store + hybrid retrieval + reranking
- Genuine iterative agent loop with enforced `max_iterations`
- Golden-dataset evaluation harness, CI-gated
- LLM observability (Langfuse / OTel GenAI conventions)
- Guardrails: prompt-injection defense, output validation, PII redaction
- Multi-provider model routing with cost-aware fallback

### Phase 3 — Enterprise & Differentiation (~8–16 weeks)

- Multi-agent architecture — specialist sub-agents + orchestrator
- MCP server exposing the Knowledge API to external agents
- Knowledge graph layer (Neo4j) for relational retrieval
- Human-in-the-loop approval workflow + review UI
- Multi-tenancy with per-tenant isolation and usage metering
- Kubernetes/Helm deployment option alongside Container Apps
- Event-driven ingestion pipeline (Kafka/Service Bus)
- Feature flags, cost dashboards, distributed cache

---

## 9. Final Verdict

A cloud-security-literate build, not yet an AI-engineering-mature one — but the gap is well-scoped and closeable.

**Strengths:** the trust-boundary architecture between agent and data is real and correctly enforced; secret handling is unusually mature (fail-closed, compromised-hash blocklisting, Key Vault + managed identity); there's a documented, tested remediation history (a regression test explicitly proving a fabricated-data fallback was removed) that shows the team responds to security findings rather than papering over them — the same instinct that led this review to fix the leaked-credential finding immediately rather than deferring it.

**Weaknesses:** the AI substance a mature platform needs — retrieval, iteration, evaluation, observability, guardrails — is either missing or simulated behind marketing language. The database layer described in the architecture doesn't exist in code. CI never gates on tests before deploying to production containers. These aren't rough edges; they're the core competencies the roadmap in this knowledge base exists to close.

**Overall audit score: 4.2 / 10**
**Engineering maturity currently demonstrated: Mid-level cloud engineering**

### Top 10 improvements, ranked by impact on technical credibility

1. **Ship real RAG** — replace keyword substring matching with embeddings + vector store + hybrid search. This is the single highest-leverage change — it's the first thing any technical stakeholder will probe.
2. **Make the agent loop actually iterate** — implement the evaluate node and enforce `max_iterations` for real — turns a decorative LangGraph skeleton into a defensible "multi-agent reasoning engine" claim.
3. **Build an evaluation harness** — a golden dataset + automated scoring, gated in CI. This is the artifact that most directly answers "how do you know your AI changes didn't break something."
4. **Add LLM observability** — trace-level cost/latency/quality visibility (Langfuse or OTel GenAI conventions) — the difference between "it works on my machine" and "here's the dashboard."
5. **Gate CI on tests before deploy** — the existing pytest suites are good; wire them into the pipeline so they actually protect production.
6. **Build the database layer for real** — a working Postgres integration closes the largest gap between the architecture diagram and the running code.
7. **Add guardrails** — prompt-injection defense and output validation — table stakes for any AI system handling retrieved external content.
8. **Add RBAC and real multi-user auth** — replace the single hardcoded admin; required before any "enterprise-ready" claim is credible.
9. **Reconcile Terraform with the running system** — wire the VNet/NSG to the actual Container Apps or remove them — fixes the one place the security story doesn't match reality.
10. **Add an MCP server** — exposing the Knowledge API over Model Context Protocol is a low-effort, high-signal way to show fluency with where agent tooling standards are heading.
