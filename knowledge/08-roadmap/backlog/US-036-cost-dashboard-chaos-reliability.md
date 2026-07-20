# US-036 — Full Observability — Cost Dashboard & Chaos-Tested Reliability

## User Story

**As a** Platform Owner / Budget Owner,  
**I want to** view a cost-per-query dashboard tracking LLM inference cost, and have the platform's reliability validated through a chaos test that confirms graceful degradation when a source connector fails,  
**So that** the platform's operational costs are transparent and its reliability behaviour is proven, not assumed.

---

## Description

This is the PI-2 completion of FEAT-11 (platform hardening), covering the remainder of the NFR-005 (Reliability) and NFR-009 (Cost optimisation) requirements deferred from PI-1. It adds a cost-per-query dashboard (using token counts captured by US-028's OTel spans) and implements and validates graceful degradation via a chaos test.

---

## Business Value

- Gives the Budget Owner the evidence needed for the ROI model: cost per query trending flat or down as volume grows.
- Proves the "graceful degradation" claim (NFR-005): returning a partial answer when one source is unavailable is better than failing the entire request.

---

## Acceptance Criteria

**Given** OTel token-cost attributes are captured per query (US-028),  
**When** the cost dashboard is viewed by a platform owner,  
**Then:**
- A dashboard shows: cost per query (in USD, estimated from input/output token counts × model pricing), cost trend over time, and cost breakdown by model (Flash vs. Pro).
- The dashboard is admin-accessible; non-engineers can read it without SQL knowledge.

**Given** the GitHub source connector's API is made unavailable (simulated by revoking the API token),  
**When** a query is submitted that would normally use GitHub content,  
**Then:**
- The query returns a partial answer drawn from wiki content only (if wiki content is relevant).
- The response includes a `source_availability_warning: ["github-unavailable"]` field.
- The response does not fail with a 5xx error.
- The chaos test result is documented and signed off.

---

## Functional Requirements

- NFR-005 (Reliability — graceful degradation).
- NFR-009 (Cost optimisation — cost-per-query dashboard).

---

## Non-Functional Requirements

- NFR-009 (Cost optimisation) — dashboard trends flat or down per unit query volume growth (reviewed at PI boundary).
- NFR-005 (Reliability) — chaos test validates graceful degradation before enterprise rollout approval.

---

## Dependencies

- US-028 (OTel tracing — token cost attributes captured here).
- US-022 (Evaluation dashboard — cost dashboard is a sibling page in the admin UI).
- US-006/US-007 (Source connectors — chaos test disables one of these).

---

## Assumptions

- Cost model: Gemini Flash at published per-token pricing; Gemini Pro at published per-token pricing. Token counts are captured as OTel span attributes.
- The cost dashboard reads from the OTel backend's stored spans (Langfuse) or from a dedicated `query_costs` aggregation table populated by a daily job.
- The chaos test is performed manually (not automated in CI); the result is documented as a test report.

---

## Edge Cases

- **Both connectors unavailable simultaneously:** The response should acknowledge that no relevant evidence was found from any available source; do not hallucinate an answer.
- **Cost dashboard shows unexpected spike:** Alert the platform owner; investigate which query types or model calls caused the spike.

---

## Technical Notes / Implementation Considerations

- **Cost calculation:** `cost = (input_tokens * flash_input_price + output_tokens * flash_output_price)` per span where `llm.model = "gemini-flash"`. Similarly for Pro. USD rates from the model's published pricing page.
- **Cost aggregation:** A `query_costs` DB view or materialized view that sums token costs per query from the `answer` records (if token counts are persisted there) or from Langfuse's API.
- **Frontend dashboard:** `CostDashboard.tsx` — a line chart of cost/query per day + a summary card showing total cost this PI.
- **Chaos test procedure:**
  1. Confirm both connectors are indexed and working.
  2. Revoke/remove the GitHub API token from the secrets store.
  3. Submit a query that normally uses GitHub content.
  4. Confirm: wiki-only partial answer returned; `source_availability_warning` present; no 5xx.
  5. Restore the GitHub token; confirm normal operation resumes.
  6. Document results in a chaos test report filed with the PI-2 exit review.
- **Graceful degradation implementation:** The retrieval endpoint must catch `ConnectorUnavailableError` per connector; exclude unavailable connectors from the merged result set; add the connector name to `source_availability_warning` in the response.

---

## Definition of Done

- [ ] Cost-per-query calculation implemented (from OTel token attributes).
- [ ] `CostDashboard.tsx` frontend page live and admin-accessible.
- [ ] Graceful degradation implemented: `ConnectorUnavailableError` caught; partial answer returned with `source_availability_warning`.
- [ ] Chaos test executed and documented (GitHub connector simulated unavailable → partial wiki answer returned, no 5xx).
- [ ] Chaos test report filed with PI-2 exit review package.
- [ ] NFR-005 and NFR-009 sign-off at PI-2 boundary review.

---

## Priority

**High** in PI-2 (NFR-005 chaos test is a non-negotiable PI-2 objective).

## Estimated Effort

**M (Medium)** — ~3–4 days (cost calculation, frontend dashboard, graceful degradation, chaos test execution and report).

## Related Epics / Features

- FEAT-11 (Platform hardening — reliability + cost)
- NFR-005 (Reliability)
- NFR-009 (Cost optimisation)
