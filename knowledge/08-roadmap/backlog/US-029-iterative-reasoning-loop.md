# US-029 — Iterative Multi-Agent Reasoning Loop (Real Evaluate / Re-Plan)

## User Story

**As a** Knowledge Worker asking a complex, multi-hop question,  
**I want to** receive an answer that the system has iterated on — re-querying when initial evidence is insufficient — rather than a single-pass best guess,  
**So that** complex questions with multiple evidence requirements are answered more accurately and completely than a single retrieval pass allows.

---

## Description

In PI-1, the agent's `should_continue` node is hardcoded to `False` (single-pass). This PI-2 story replaces that stub with a real evaluate/re-plan loop: after the first evidence retrieval, the agent evaluates whether the evidence is sufficient to answer the query, and if not, generates follow-up sub-queries and retrieves additional evidence, bounded by `max_iterations`. This directly closes the "stub — evaluation node is a no-op" finding from the [EVIKAP audit](../../EVIKAP_AUDIT.md).

---

## Business Value

- Replaces the largest outstanding gap in agent capability with a genuine implementation.
- Directly satisfies FR-004's acceptance check: "on the multi-hop subset of the golden evaluation dataset, iterative retrieval measurably outperforms a single-pass baseline."
- Enables the platform to handle the relationship-type questions (e.g., "what services depend on X, and are they all using the latest schema?") that the MVP's single-pass synthesis cannot answer reliably.

---

## Acceptance Criteria

**Given** a multi-hop query (e.g., "What authentication method does service A use, and does service B share any authentication infrastructure with it?"),  
**When** the agent processes the query with `max_iterations=3`,  
**Then:**
- The agent evaluates whether the first pass's evidence is sufficient to fully answer the query.
- If not sufficient, the agent generates ≥1 follow-up sub-query and retrieves additional evidence.
- The loop terminates when: (a) evidence is judged sufficient, or (b) `max_iterations` is reached (whichever comes first).
- `max_iterations` is enforced — the loop cannot run indefinitely regardless of evidence sufficiency evaluation.
- On the multi-hop subset of the golden evaluation dataset, RAGAS `context_recall` is measurably higher (≥5pp improvement) with iteration enabled vs. the single-pass PI-1 baseline.
- The hardcoded `False` stub and its TODO comment are removed.

---

## Functional Requirements

- FR-004 (Multi-agent iterative reasoning) — full implementation replacing the PI-1 stub.

---

## Non-Functional Requirements

- NFR-006 (Performance) — iterative queries have higher latency; this is expected. The p50 latency target for multi-hop queries is set at 2× the single-hop target (e.g., ≤12 seconds for `max_iterations=3`).
- NFR-009 (Cost optimisation) — each iteration adds LLM calls; track cost per iteration in OTel spans.
- NFR-010 (Maintainability) — `max_iterations` is configurable via env var, not hardcoded.

---

## Dependencies

- US-008 (Hybrid retrieval endpoint — called per sub-query iteration).
- US-023 (CI-gated evaluation — the regression gate must run with iteration enabled; the threshold may need updating after the first iterative evaluation run).
- US-028 (OTel tracing — iteration count and per-iteration latency captured as span attributes).

---

## Assumptions

- The `evaluate` node uses the LLM itself (Gemini Flash) to assess sufficiency: "Given the query and the retrieved evidence, is there enough information to fully answer the question? Answer yes or no, and if no, list what is still missing."
- `max_iterations` default is 3; configurable via `AGENT_MAX_ITERATIONS` env var.
- Sub-query generation uses the LLM to decompose the "still missing" items into specific follow-up queries.
- The golden dataset is augmented with ≥5 multi-hop cases (seeded as `EvaluationCase` records with `tags: ["multi-hop"]`) before this story's acceptance test is run.

---

## Edge Cases

- **LLM always judges evidence as insufficient (pathological case):** `max_iterations` is the hard ceiling; the loop must terminate regardless. Log a warning: "max_iterations reached without sufficient evidence."
- **Sub-query generates no new evidence (same chunks retrieved again):** Detect by comparing `chunk_id` sets between iterations; terminate early if the retrieved set is identical.
- **`max_iterations=1` (effectively single-pass):** Must work identically to the PI-1 single-pass behaviour.

---

## Technical Notes / Implementation Considerations

- **LangGraph changes:** Replace `should_continue()` returning `False` with a real implementation:
  ```python
  def evaluate(state) -> state:
      sufficient = llm.assess_sufficiency(state.query, state.evidence)
      return state.update(sufficient=sufficient, iteration=state.iteration + 1)
  
  def should_continue(state) -> bool:
      return not state.sufficient and state.iteration < state.max_iterations
  ```
- **State updates:** `AgentState` (in `agent/app/graph.py`) needs `iteration: int = 0`, `sufficient: bool = False`, `sub_queries: list[str]`, `all_evidence: list[EvidenceItem]` (accumulated across iterations).
- **Sub-query generation:** A new LangGraph node `decompose` → calls `llm.generate_sub_queries(query, missing_items)` → returns a list of sub-queries for the next `execute` pass.
- **Evidence accumulation:** Evidence from all iterations is merged and deduplicated (by `chunk_id`) before being passed to synthesis.
- **OTel:** Add `agent.iteration_count` and `agent.sufficient` as span attributes.

---

## Definition of Done

- [ ] `should_continue()` stub replaced with a real evaluate/re-plan loop.
- [ ] `max_iterations` enforced; configurable via `AGENT_MAX_ITERATIONS` env var.
- [ ] Identical-evidence early termination implemented.
- [ ] `AgentState` updated with iteration tracking fields.
- [ ] OTel span attributes: `agent.iteration_count`, `agent.sufficient`.
- [ ] RAGAS `context_recall` on multi-hop evaluation subset ≥5pp improvement vs. single-pass baseline confirmed.
- [ ] CI evaluation gate updated with new threshold (if improved quality raises the baseline).
- [ ] Unit tests: max_iterations enforced; early termination on identical evidence; single-pass (`max_iterations=1`) behaviour unchanged.
- [ ] CI passes.

---

## Priority

**High** — Core FR-004 requirement; PI-2 must-have.

## Estimated Effort

**L (Large)** — ~5–8 days (LangGraph rework, state management, LLM sufficiency evaluation, sub-query generation, evaluation done-check).

## Related Epics / Features

- FEAT-04 (Iterative multi-agent reasoning)
- FR-004
- NFR-009 (Cost optimisation — iteration cost tracking)
