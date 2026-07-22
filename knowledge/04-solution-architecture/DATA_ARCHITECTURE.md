# Data Architecture

**TOGAF ADM Phase C — Information Systems Architecture (Data)**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../02-business-architecture/BUSINESS_ARCHITECTURE.md](../02-business-architecture/BUSINESS_ARCHITECTURE.md) · [APPLICATION_ARCHITECTURE.md](APPLICATION_ARCHITECTURE.md)

---

## 1. Purpose

Defines what data VigilRAG holds, where source data lives, how it flows, and how it is classified and governed — independent of the specific database/vector-store product chosen.

## 2. Data domains

| Domain | Description | System of record | Owned by VigilRAG? |
|---|---|---|---|
| Source content (code, docs, wiki pages, schema DDL) | The actual enterprise knowledge being indexed | External source systems (repo host, wiki, database) | No — indexed, not owned |
| Retrieval index (embeddings, chunk metadata, keyword index) | Derived representation enabling semantic + keyword search | VigilRAG | Yes |
| Query and session data | User/agent queries, decomposition plans, retrieved evidence per request | VigilRAG | Yes |
| Audit and provenance log | Who asked what, what evidence was used, what was answered | VigilRAG | Yes |
| Source registry and classification | Registered sources, their sensitivity classification, refresh cadence | VigilRAG | Yes |
| Identity and permission cache | Mapping of requester identity to source-system permissions, used to enforce FR-006 | VigilRAG (cache), source IdP (authoritative) | Cache only |
| Evaluation dataset | Golden query/answer pairs used to gate quality (NFR-010, NFR-011) | VigilRAG | Yes |
| Evaluation results | Per-run RAGAS/DeepEval scores (faithfulness, context-precision, context-recall) per pipeline version | VigilRAG | Yes |
| Model/System Cards | Published metadata per pipeline version: purpose, limitations, eval scores, last-updated (FR-013) | VigilRAG | Yes |
| Knowledge graph (roadmap — see §5.1) | Entities and relationships extracted from source content, for relational queries vector similarity can't answer | VigilRAG (derived, Phase 4+ / FEAT-13) | Yes, once built |

## 3. Current-state gap (from audit)

The existing implementation has **no data layer of its own** for the "database" source type — `DatabaseSubsystem.query_schemas()` performs a GitHub filename search rather than querying an actual database, despite the architecture being advertised as including SQL databases as a first-class source (see [audit §5](../VigilRAG_AUDIT.md)). This data architecture supersedes that gap: Section 5 below specifies the real database requirement.

## 4. Conceptual data flow

```
Source systems (code, wiki, DB schemas)
      |  (read-only, least-privilege, per-source credentials held ONLY by the retrieval/backend tier)
      v
Indexing pipeline --> chunking --> embedding --> [ Retrieval Index: vector + keyword ]
                                                          |
Query (human/agent) --> Query & Session store <-- retrieval-time lookup
      |
      v
Agent orchestration (plan/execute/evaluate/respond) --> Audit & Provenance log
      |
      v
Synthesized, cited answer
```

The trust-boundary principle from the Architecture Vision applies directly here: **the agent/orchestration tier never touches source-system credentials or the raw retrieval index directly** — it calls the retrieval tier's API, which is the only component with source-system access.

## 5. Logical data entities (initial)

| Entity | Key attributes | Notes |
|---|---|---|
| `Source` | id, type, connection_ref, sensitivity_classification, refresh_cadence, owner | Registry entity backing FR-007 |
| `Document` / `Chunk` | id, source_id, content, embedding_vector, permissions_ref, last_indexed_at, checksum | Checksum enables staleness/change detection for FR-005 |
| `Query` | id, requester_identity, text, timestamp | |
| `EvidenceItem` | query_id, chunk_id, relevance_score, rerank_score, used_in_answer (bool) | Backbone of provenance (FR-003, FR-008); `rerank_score` populated by the FR-011 reranking step, distinct from the initial retrieval `relevance_score` so reranking's contribution is itself measurable |
| `Answer` | query_id, synthesized_text, citations[], groundedness_score, guardrail_flags[] | `guardrail_flags` records any FR-012 guardrail intervention (e.g., injected-instruction neutralized, output rejected and regenerated) for audit purposes |
| `PermissionCache` | requester_identity, source_id, access_level, cached_at, ttl | Must never be treated as authoritative beyond its TTL — re-verify against source IdP on a defined cadence |
| `EvaluationCase` | id, golden_query, golden_answer, tags | Backs the evaluation harness (NFR-011) |
| `EvaluationRun` | id, pipeline_version, dataset_version, faithfulness, context_precision, context_recall, run_at | One row per CI/production evaluation run; the source of truth a Model/System Card's published scores must match |
| `ModelCard` | pipeline_version, purpose, capabilities, known_limitations, eval_run_id (fk), published_at | Backs FR-013; `eval_run_id` ties the card to a specific `EvaluationRun` so scores can never drift from what was actually measured |

### 5.1 Future entities — knowledge graph (roadmap, FEAT-13)

Not built in the current scope, but named here so the target data model doesn't need re-architecture when this phase arrives: `Entity` (id, type, name, source_chunk_ids[]) and `Relationship` (from_entity_id, to_entity_id, relationship_type, source_chunk_ids[]), populated by an extraction step over indexed content and queried via a graph store (see [Technology Architecture §3](TECHNOLOGY_ARCHITECTURE.md#3-target-technology-stack-by-layer)) *alongside*, not instead of, the vector retrieval index — a GraphRAG pattern where relational questions ("which services depend on this schema") route to the graph and semantic-similarity questions continue to route to vector retrieval.

#### Graph-Ready Ingestion Requirements (Phase 1 Constraints)
To ensure the system is ready to adapt to the Knowledge Graph in later phases, the Phase 1 ingestion pipeline and vector schemas must satisfy these constraints:
1. **Hierarchical and Relational Metadata:** Every document chunk must capture metadata for `parent_doc_id` (to track document sections/structure) and a list of `references[]` (to track explicit dependencies like code imports, page links, or shared concepts).
2. **Ingestion Preservation:** The parser must identify and extract these relations during the ingestion step and write them into the database alongside the vector embedding.
3. **Query Engine Modularity:** The query routing service must be designed using a routing pattern (e.g., broker or query planner interface) so that adding the Neo4j query engine later is a drop-in integration without modifying core application code.

## 6. Data classification and handling

| Classification | Examples | Handling requirement |
|---|---|---|
| Public/internal-general | Public docs, general wiki pages | Standard indexing, no special controls |
| Internal-sensitive | Architecture decisions, unreleased roadmaps | Indexed with source-permission propagation strictly enforced |
| Regulated (PII/PHI/financial) | Customer records in structured sources | Not onboarded until [Compliance & Security Framework](../07-governance-risk/COMPLIANCE_SECURITY_FRAMEWORK.md) redaction and audit controls are verified for that source type |

Classification is assigned at source-registration time (FR-007) by the source owner, per [Business Architecture §4](../02-business-architecture/BUSINESS_ARCHITECTURE.md#4-organizational-impact).

## 7. Data quality and lifecycle

- **Freshness:** each chunk carries `last_indexed_at` and a `checksum`; a scheduled re-index job detects source changes and triggers re-embedding — this is the mechanism behind FR-005 (freshness/conflict signaling).
- **Retention:** query/session and audit data retained per the organization's compliance policy (NFR-004); retrieval index data retained as long as the source registration is active, purged on source de-registration.
- **Deletion propagation:** when content is deleted or access-restricted at the source, the corresponding chunk must be purged or re-permissioned from the retrieval index within a defined SLA (to be set during discovery) — an explicit requirement to prevent the retrieval index from becoming a stale, ungoverned shadow copy of restricted content.

## 8. Relationship to technology choices

This document intentionally does not name a specific vector database or storage product — that decision, including the explicit trigger criteria for graduating from a co-located vector store to a dedicated one, belongs to [TECHNOLOGY_ARCHITECTURE.md §6a](TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path), which must satisfy the entities, flows, and classification rules defined here regardless of which product is chosen.
