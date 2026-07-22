# Business Architecture

**TOGAF ADM Phase B — Business Architecture**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../01-architecture-vision/ARCHITECTURE_VISION.md](../01-architecture-vision/ARCHITECTURE_VISION.md) · [STAKEHOLDER_ANALYSIS.md](STAKEHOLDER_ANALYSIS.md)

---

## 1. Purpose

Defines the business capabilities, value streams, and organizational functions VigilRAG must support, independent of any technology choice. This is the bridge between the business problem and the solution/technology architecture phases.

## 2. Business capability model

| Capability | Description | Currently exists? | Owned by (post-delivery) |
|---|---|---|---|
| Knowledge source registration | Onboard a new source system (repo, wiki space, database schema) for indexing | No | Platform team |
| Cross-source semantic retrieval | Find relevant evidence across all registered sources for a natural-language query | No (keyword/substring only today — see [audit](../VigilRAG_AUDIT.md)) | Platform team |
| Governed AI reasoning | Decompose a question, gather evidence iteratively, synthesize a cited answer | Partially — single-pass only today | Platform team |
| Permission-aware access enforcement | Ensure retrieval respects each source system's existing access control | Partially — trust boundary exists between agent and backend, but no RBAC | Security engineering |
| Answer provenance & audit | Record what was asked, by whom, and which evidence contributed to the answer | No | Platform team / Compliance |
| Quality evaluation & continuous improvement | Measure and gate retrieval/answer quality before and after production changes | No | AI engineering |
| Knowledge freshness & conflict management | Detect and surface stale or contradictory source content | No | Platform team, with source owners |
| Machine (agent) tool access | Expose the platform as a callable tool for other internal AI agents | Partially — internal API exists, no standardized (MCP) interface | Platform team |

## 3. Value streams

### 3.1 Primary value stream — "Get a trustworthy answer"

```
Question posed (human or agent)
      -> Query understood & decomposed
      -> Evidence retrieved across permitted sources
      -> Evidence evaluated for sufficiency (iterate if not)
      -> Answer synthesized with citations
      -> Answer delivered + logged for audit
      -> [optional] Feedback captured -> feeds evaluation harness
```

**Value stage owners and current maturity:**

| Stage | Business capability invoked | Current maturity |
|---|---|---|
| Query understood & decomposed | Governed AI reasoning | Stub — no real decomposition/iteration |
| Evidence retrieved | Cross-source semantic retrieval | Weak — keyword/substring, no ranking |
| Evidence evaluated for sufficiency | Governed AI reasoning | Absent — evaluation node is a no-op |
| Answer synthesized with citations | Governed AI reasoning | Partial — synthesis exists, citation discipline not enforced |
| Answer logged for audit | Answer provenance & audit | Absent |
| Feedback feeds evaluation | Quality evaluation | Absent |

### 3.2 Secondary value stream — "Onboard a new knowledge source"

```
Source identified by business owner
      -> Access/credentials provisioned (least privilege)
      -> Source classified (data sensitivity, refresh cadence)
      -> Source indexed
      -> Source available in retrieval layer
      -> Source health monitored (staleness, index failures)
```

This value stream does not exist today in any form — there is no source-registration workflow, only hardcoded source integrations in application code.

## 4. Organizational impact

| Function | Change required |
|---|---|
| Platform/AI engineering | New team responsibility: own retrieval quality, evaluation harness, and agent orchestration as an ongoing product, not a one-time build |
| Security engineering | New responsibility: certify each source connector's permission-propagation correctness before it goes live |
| Source system owners (repo admins, wiki admins, DBAs) | New light-touch responsibility: classify their system's content sensitivity and approve indexing scope |
| Compliance | Gains a new auditable system to include in AI-governance review; loses the current blind spot of ungoverned AI-to-data access |
| End users | Behavior change: default to asking VigilRAG before searching individual systems or interrupting colleagues — requires an adoption/change-management motion, not just a technical rollout |

## 5. Business process alignment

VigilRAG does not replace any existing business process; it inserts itself as a new step ahead of the informal "guess the system, search, ask a colleague" process described in [Problem Statement §3.2](../PRODUCT_PROBLEM_STATEMENT.md#32-current-business-processes). Success is measured by the degree to which that informal process is displaced (see adoption metrics in [Problem Statement §12.4](../PRODUCT_PROBLEM_STATEMENT.md#124-user-adoption-metrics)).

## 6. Relationship to data, application, and technology architecture

This business architecture is realized by:

- **Data architecture** — [../04-solution-architecture/DATA_ARCHITECTURE.md](../04-solution-architecture/DATA_ARCHITECTURE.md)
- **Application architecture** — [../04-solution-architecture/APPLICATION_ARCHITECTURE.md](../04-solution-architecture/APPLICATION_ARCHITECTURE.md)
- **Technology architecture** — [../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md](../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md)

Each capability gap identified in Section 2 above is the direct input to the functional requirements in [../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md](../03-business-analysis/FUNCTIONAL_REQUIREMENTS_SPECIFICATION.md).
