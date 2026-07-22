# Functional Requirements Specification

**BABOK — Requirements Analysis and Design Definition**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [../PRODUCT_PROBLEM_STATEMENT.md §6](../PRODUCT_PROBLEM_STATEMENT.md#6-functional-requirements) · [REQUIREMENTS_MANAGEMENT_PLAN.md](REQUIREMENTS_MANAGEMENT_PLAN.md)

---

## 1. Purpose and notation

Each requirement is stated in testable form with an acceptance check. IDs are stable and referenced from the traceability matrix — do not renumber; retire and add new IDs instead.

## 2. Requirements

### FR-001 — Unified query interface

**Statement:** The system shall provide a single interface (UI and API) through which a user or AI agent submits a natural-language question and receives one synthesized response drawn from all in-scope, permitted sources.
**Acceptance check:** A query touching two or more distinct source types returns a single response, not multiple per-source responses requiring manual reconciliation.

### FR-002 — Cross-source semantic retrieval

**Statement:** The system shall retrieve relevant evidence using semantic (meaning-based) matching in addition to keyword matching, across all registered source types.
**Acceptance check:** For a query phrased differently from the source document's wording but matching its meaning, the correct source is retrieved in the top-k results. (This directly closes the gap identified in the [audit](../VigilRAG_AUDIT.md): current retrieval is keyword/substring only.)

### FR-003 — Provenance and citation

**Statement:** Every claim in a synthesized answer shall be traceable to a specific cited source (document, file, or record) with a link back to the system of record.
**Acceptance check:** Automated groundedness evaluation (see [NFR](NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md)) confirms ≥90% of answer claims map to a retrieved, cited source on the golden evaluation dataset.

### FR-004 — Multi-agent iterative reasoning

**Statement:** The system shall decompose complex, multi-hop questions into sub-queries, execute them, evaluate whether gathered evidence is sufficient, and iterate (re-plan/re-query) when it is not, up to a configurable and enforced iteration limit.
**Acceptance check:** On the multi-hop subset of the golden evaluation dataset, iterative retrieval measurably outperforms a single-pass baseline; the `max_iterations` parameter demonstrably bounds actual loop behavior (closes the "accepted but never enforced" gap identified in the audit).

### FR-005 — Freshness and conflict signaling

**Statement:** When retrieved sources disagree, or the most relevant source appears stale relative to newer sources on the same topic, the system shall surface that signal in the response rather than silently presenting one source as authoritative.
**Acceptance check:** A test fixture with two conflicting source documents produces a response that flags the conflict and cites both.

### FR-006 — Permission-aware retrieval

**Statement:** The system shall never return, cite, or synthesize from content the requesting identity (human or service identity) could not already access directly in the source system.
**Acceptance check:** A permission-matrix test suite (per source connector) confirms zero over-exposure across a representative set of restricted/unrestricted content pairs.

### FR-007 — Source registration workflow

**Statement:** The system shall provide an administrative workflow to register a new knowledge source (type, connection details, indexing scope, refresh cadence, sensitivity classification) without requiring a code change per source.
**Acceptance check:** A new source of an already-supported type (e.g., a second wiki space) can be onboarded through the workflow in under one business day of administrative effort.

### FR-008 — Audit and access review

**Statement:** The system shall log every query, the identity that issued it, the sources and records that contributed evidence, and the resulting answer, in a form retrievable for compliance review.
**Acceptance check:** A compliance reviewer can answer "what did identity X see when they asked Y on date Z" from the audit log alone, without engineering assistance.

### FR-009 — Feedback and correction loop

**Statement:** The system shall allow a user to flag a response as incorrect, outdated, or ungrounded, and route that feedback into the evaluation dataset/pipeline.
**Acceptance check:** A flagged response appears in the evaluation-harness review queue within one indexing cycle.

### FR-010 — Standards-based machine (agent) interface

**Statement:** The system shall expose its query capability as a tool conforming to a standard agent-tool protocol (e.g., Model Context Protocol), in addition to its human-facing UI, so external AI agents can integrate without bespoke per-agent adapters.
**Acceptance check:** A reference external agent can discover and successfully invoke the tool using only the published standard interface contract, with no VigilRAG-specific client code.

### FR-011 — Retrieval reranking

**Statement:** After initial hybrid (semantic + keyword) retrieval, the system shall apply a reranking step that re-orders candidate evidence by relevance to the query before it is passed to synthesis, using a cross-encoder or dedicated reranking model rather than relying solely on the initial retrieval score.
**Acceptance check:** Top-k relevance on the golden evaluation dataset (see [NFR-011](NONFUNCTIONAL_REQUIREMENTS_SPECIFICATION.md)) is measurably higher with reranking enabled than with the same retrieval step and reranking disabled.

### FR-012 — Guardrails: prompt-injection defense and output validation

**Statement:** The system shall detect and neutralize prompt-injection attempts contained in retrieved source content before that content reaches the synthesis model, and shall validate synthesized output against a structural/safety schema before returning it to the caller.
**Acceptance check:** A maintained test suite of known prompt-injection patterns embedded in fixture source documents is blocked or neutralized (the injected instruction has no effect on the synthesized answer); a fixture producing a malformed or unsafe output is rejected before delivery rather than returned to the caller.

### FR-013 — Model/System Card publication

**Statement:** Each deployed version of the retrieval and agent-orchestration pipeline shall have an associated, versioned Model/System Card documenting its purpose, capabilities, known limitations, current evaluation scores, and last-updated date, published alongside the release.
**Acceptance check:** For any production release, a reviewer can locate a current Model/System Card for that exact version without engineering assistance, and the scores on the card match the evaluation harness's own record for that version.

## 3. Representative user workflows

Full narrative in [Problem Statement §6.2](../PRODUCT_PROBLEM_STATEMENT.md#62-user-workflows). Each maps to the requirements above:

| Workflow | Requirements exercised |
|---|---|
| Ask a question (human, interactive) | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-011, FR-012 |
| Ask a question (machine, MCP) | FR-001, FR-002, FR-003, FR-004, FR-006, FR-010, FR-011, FR-012 |
| Source registration | FR-007 |
| Access and audit review | FR-006, FR-008 |
| Feedback and correction | FR-009 |
| Release and governance review | FR-013 |

## 4. Explicitly out of scope for this specification

Write-back to source systems, predictive/proactive knowledge surfacing, and knowledge-graph reasoning are deferred — see [Problem Statement §10.2–10.3](../PRODUCT_PROBLEM_STATEMENT.md#102-out-of-scope-initial-delivery) and are not assigned FR IDs in this baseline.
