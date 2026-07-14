# Technology Architecture

**TOGAF ADM Phase D — Technology Architecture**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [APPLICATION_ARCHITECTURE.md](APPLICATION_ARCHITECTURE.md) · [../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md)

---

## 1. Purpose

Specifies the infrastructure, platform, and product choices that realize the application architecture, and reconciles them with what is already running (Azure Container Apps, Terraform) per the current build.

## 2. Technology principles

| Principle | Statement |
|---|---|
| Reuse existing platform investment | Target infrastructure is the organization's existing cloud/container platform (Azure Container Apps, per current build) unless a specific NFR cannot be met there |
| Infrastructure as Code is authoritative | No manually-applied infrastructure change; Terraform state must match running infrastructure — closing the drift the audit identified between provisioned VNet/NSGs and the actual (external, pre-existing) Container App environment |
| Managed services over self-hosted where viable | Prefer managed vector store / managed Postgres / managed Key Vault over self-hosted equivalents to reduce operational burden on a small platform team |
| Portability is a roadmap concern, not an MVP requirement | Kubernetes portability is deferred (see [Problem Statement §10.2](../PRODUCT_PROBLEM_STATEMENT.md#102-out-of-scope-initial-delivery)) unless multi-cloud becomes a stated requirement |

## 3. Target technology stack by layer

| Layer | Current state | Target state | Rationale for change |
|---|---|---|---|
| Compute | Azure Container Apps (3 services) | Azure Container Apps, corrected to actually run inside the provisioned VNet/NSG (fixing the drift) | Realizes the network-isolation claim already documented but not actually wired |
| Relational data | None (advertised, not implemented) | Managed PostgreSQL (e.g., Azure Database for PostgreSQL) | Closes the fictional "SQL database source" gap (see [Data Architecture §3](DATA_ARCHITECTURE.md#3-current-state-gap-from-audit)) |
| Vector/retrieval index | None | Managed vector store — **pgvector** on the same Postgres instance at MVP scale, with an explicit graduation path to a dedicated vector DB (see [§6a](#6a-vector-database-graduation-path)) | Required for FR-002 (semantic retrieval) |
| Reranking | None | Cross-encoder reranking model (e.g., **bge-reranker**, self-hosted) or a managed reranking API (e.g., **Cohere Rerank**) applied after initial hybrid retrieval | Required for FR-011 |
| RAG evaluation framework | None (manual narrative only) | **RAGAS** (faithfulness, context-precision, context-recall) as the primary framework, with **DeepEval** or an equivalent LLM-as-judge harness as a fallback for metrics RAGAS doesn't cover | Required for NFR-011; this is the concrete tool behind the "evaluation harness" referenced throughout this knowledge base |
| Guardrails | None | **Guardrails AI** or **NVIDIA NeMo Guardrails** for prompt-injection defense and structured output validation; **Microsoft Presidio** for PII detection/redaction (distinct concern from injection defense, see NFR-003) | Required for FR-012 |
| Knowledge graph (roadmap, FEAT-13) | None | **Neo4j** as the graph store, populated via an entity/relationship extraction step, queried through a GraphRAG pattern (e.g., Microsoft's GraphRAG approach or LlamaIndex's property graph index) that routes relational questions to the graph and similarity questions to vector retrieval — the two are complementary, not competing | Closes relationship-shaped questions ("which services depend on this schema") that vector similarity alone cannot answer |
| Prompt management | Hardcoded strings in `graph.py` | Git-versioned prompt templates, promoted to production only after passing the RAGAS/DeepEval evaluation gate (no separate prompt-management product required at this scale; a dedicated registry like Langfuse's prompt management is a later option if prompt volume grows) | Required for NFR-010/NFR-011 — prompt changes must be as auditable and reversible as code changes |
| Distributed cache | None (unbounded in-process dict) | Managed Redis (e.g., Azure Cache for Redis) | Replaces the memory-leak-shaped, non-shared cache identified in the audit; required for horizontal scale-out (NFR-001) |
| Secrets management | Azure Key Vault + managed identity | Unchanged — already a genuine strength | No change needed |
| LLM provider(s) | Gemini only, with dead OpenAI config | Gemini as primary, with a second provider wired as a real fallback (not dead config) | Required for NFR-009 (cost) and reliability under provider outage |
| Observability | stdlib logging only | OpenTelemetry (GenAI semantic conventions) exporting to a dedicated LLM observability platform — **Langfuse** as the primary choice (self-hostable, first-class RAGAS integration), **Arize Phoenix** as an alternative | Required for NFR-007; currently only aspirational documentation, not implemented, per the audit |
| CI/CD | GitHub Actions, build-and-deploy, no test gate | GitHub Actions with a mandatory test + evaluation-harness gate before deploy | Required for NFR-010 and closes the audit's most consequential production-readiness gap |
| Agent tool protocol | None | Model Context Protocol (MCP) server wrapping the Knowledge API | Required for FR-010 |
| Governance artifacts | None | Model/System Card generated per release from the evaluation service's `EvaluationRun` record (see [Data Architecture §5](DATA_ARCHITECTURE.md#5-logical-data-entities-initial)); governance framework mapped to **NIST AI RMF** or **ISO/IEC 42001** | Required for FR-013, NFR-012 |

## 4. Infrastructure topology (target)

```
                    +-------------------+
   Internet ------> |  Interface tier   |  (public ingress)
                    +-------------------+
                              |
                              v  (internal only)
                    +-------------------+        +--------------------+
                    |  Knowledge API    |<------>|  Postgres + pgvector|
                    |  (retrieval tier, |        |  (source registry,  |
                    |  incl. reranker)  |        |   audit log)        |
                    +-------------------+        +--------------------+
                        |         |
                        v         v
              +----------------+  +----------------+
              | Guardrails svc |  | Redis (shared   |
              | (evidence-in / |  | query cache)    |
              | answer-out)    |  +----------------+
              +----------------+
                        |
                        v
              +----------------+
              | Agent orch.    |
              | tier (no       |
              | external       |
              | ingress)       |
              +----------------+
                   |        |
                   v        v
     +----------------+  +----------------------------+
     | Evaluation svc |  | MCP gateway (internal AI    |
     | (RAGAS/DeepEval|  | agent consumers)            |
     | + Model/System |  +----------------------------+
     | Card publisher)|
     +----------------+

All services: Key Vault + managed identity for secrets;
OpenTelemetry traces -> Langfuse (+ Azure Monitor); deployed
inside the provisioned VNet with NSG-enforced egress control.
Neo4j (knowledge graph, roadmap/FEAT-13) sits alongside
Postgres once built — see §6a and Data Architecture §5.1.
```

## 5. Non-functional requirement to technology mapping

| NFR | Technology decision that satisfies it |
|---|---|
| NFR-001 Scalability | Container Apps horizontal autoscale; Redis shared cache removes the per-process bottleneck |
| NFR-002 Security | Trust-boundary network topology (no external ingress on orchestration tier); Key Vault + managed identity |
| NFR-005 Reliability | Multi-provider LLM fallback; graceful-degradation logic in the orchestration tier |
| NFR-007 Observability | OpenTelemetry GenAI conventions end-to-end |
| NFR-008 Availability | Existing health-probe pattern retained and extended to all new services |
| NFR-009 Cost optimization | Model routing policy + per-query cost tagging in observability pipeline |
| NFR-010 Maintainability | CI evaluation gate; Terraform-managed infrastructure with drift detection |
| NFR-011 AI Quality Assurance | RAGAS/DeepEval evaluation service, gating CI and feeding a production quality-trend dashboard in Langfuse |
| NFR-012 Governance and transparency | Model/System Card publisher sourced from `EvaluationRun` records; governance mapping to NIST AI RMF / ISO/IEC 42001 |

## 6. Deployment profiles

Sections 2–5 above describe a single target architecture, but two distinct, non-interchangeable deployment profiles exist for this project and must not be conflated:

| | **Enterprise/Target profile** | **Demo/Low-Cost profile** |
|---|---|---|
| Purpose | The architecture this knowledge base is written for — a governed pilot/production deployment inside a sponsoring organization's cloud | A low-cost, publicly-reachable environment for demonstrating the product to stakeholders without provisioning enterprise infrastructure |
| Stack | Azure Container Apps, managed Postgres/pgvector, managed Redis, Key Vault + managed identity, OpenTelemetry → Azure Monitor (Sections 2–5) | Netlify (frontend static hosting), Koyeb (backend + agent containers, free-tier Nano instance), Supabase (managed Postgres) — see `deployment/deployment_plan.md` |
| NFR conformance | Designed to meet the full NFR set in [Non-Functional Requirements Specification](../03-business-analysis/NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md) | **Explicitly does not** meet NFR-001 (scalability — single free-tier instance), NFR-008 (99.5%+ availability — no SLA on free tiers), or NFR-009 (cost optimization — not a cost model at production volume); acceptable only because no real user or regulated data is served in this profile |
| Trust boundary (Architecture Vision §7) | Fully enforced — no reasoning component holds source credentials | Must still be fully enforced — the trust boundary is a correctness/security property of the application architecture, not an infrastructure-scale property, so it is **not** relaxed in the demo profile even though performance/availability guarantees are |
| Data sensitivity | May progress to internal-sensitive and (with sign-off) regulated sources per [Compliance & Security Framework](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md) | Public/synthetic or non-sensitive demo content only — never a source containing real internal or regulated data |
| Known gap as of this writing | Terraform/runtime drift (Section 7) | `deployment/deployment_plan.md` assumes a working SQLAlchemy/Postgres connection (`"✓ Settings initialized: DATABASE_URL loaded"`), but `backend/requirements.txt` does not include `sqlalchemy`/`asyncpg`/`psycopg2` — the plan is currently aspirational in the same way the Azure deployment doc was, until the real database layer from [Data Architecture §3](DATA_ARCHITECTURE.md#3-current-state-gap-from-audit) is implemented |

**Why both are kept:** the enterprise profile is what this knowledge base's requirements and acceptance criteria are written against and is the only profile suitable for a real pilot; the demo profile exists purely so the product can be shown running publicly at near-zero cost. Neither should be read as a substitute for the other — a stakeholder evaluating production readiness should be pointed at the enterprise profile, and cost/scale claims from one profile must never be quoted as evidence for the other.

## 6a. Vector database graduation path

Starting on pgvector (co-located with Postgres) is the right MVP choice — it minimizes operational surface area and keeps the source registry, audit log, and retrieval index in one transactionally-consistent store. It is **not** the right choice indefinitely. This section defines the trigger criteria for migrating to a dedicated vector database (e.g., **Qdrant** or **Weaviate**) so that decision is made deliberately, against evidence, rather than reactively during an incident.

| Signal | Threshold that triggers evaluation | Why pgvector degrades here |
|---|---|---|
| Corpus size | Approaching ~1M+ chunks | pgvector's HNSW/IVFFlat index performance and build time degrade faster than purpose-built ANN indexes at this scale |
| Query latency | p90 retrieval latency trending toward the NFR-006 budget with retrieval, not synthesis, as the dominant cost | Signals the index structure itself is the bottleneck, not model latency |
| Filtering complexity | Retrieval increasingly needs rich metadata pre-filtering (per-tenant, per-classification, per-source) combined with vector search | Dedicated vector DBs generally have more mature hybrid filter+ANN query planners than pgvector at this combination |
| Operational load | Postgres is simultaneously serving as the vector index, the source registry, and the audit log under real production write volume | Separating the vector workload avoids one workload's resource contention degrading the others |

**Decision rule:** if two or more signals are met, open a PI-level spike to evaluate migration; do not migrate speculatively on a single signal, and do not defer migration once two or more are actually met — both premature and delayed migration are risks (see [Risk Register](../07-governance-risk/RISK_REGISTER.md)). This graduation decision is independent of, and does not require, the knowledge-graph addition (FEAT-13) — the two are separate stores serving separate query shapes (similarity vs. relationship), not sequential upgrades of the same thing.

## 7. Migration note on existing infrastructure

The current Terraform configuration provisions a VNet/NSG that the running Container Apps do not actually use (they run in a separate, pre-existing environment borrowed from another project). This technology architecture requires that drift be resolved as an early implementation task — either by migrating the running services into the provisioned network, or by removing the unused network resources and documenting the real (interim) network posture honestly — before any regulated-data source is onboarded. See [08-roadmap](../08-roadmap/MIGRATION_IMPLEMENTATION_ROADMAP.md) for sequencing.
