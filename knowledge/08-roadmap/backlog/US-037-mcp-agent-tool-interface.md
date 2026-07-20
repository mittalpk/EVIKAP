# US-037 — MCP-Based Agent Tool Interface

## User Story

**As an** AI Agent developer (e.g., a coding assistant or support copilot team),  
**I want to** discover and invoke EVIKAP's knowledge query capability through a standard Model Context Protocol (MCP) tool interface,  
**So that** I can integrate EVIKAP into my agent without writing any EVIKAP-specific client code — using only the published MCP standard.

---

## Description

This story implements FR-010: exposing EVIKAP's `/api/v1/query` capability as a standards-based MCP tool. The MCP gateway is a protocol adapter that wraps the existing internal query API — it does not implement a parallel query path. External AI agents discover the tool via the MCP tool manifest and invoke it using standard MCP request/response conventions. The gateway enforces the same authentication and permission controls as the human UI.

---

## Business Value

- Opens EVIKAP to machine (agent) consumers — a distinct consumer segment from human knowledge workers.
- Satisfies FR-010 acceptance check: "a reference external agent can discover and invoke the tool using only the published standard interface contract, with no EVIKAP-specific client code."
- Sequenced to PI-3 deliberately (per [MVP Definition §4](../../05-lean-product/MVP_DEFINITION.md#4-explicitly-deferred-past-mvp)) so machine-consumer validation is not confounded with human-consumer validation in PI-1.

---

## Acceptance Criteria

**Given** the MCP gateway is deployed and the tool manifest is published,  
**When** a reference external MCP-compatible agent (e.g., Claude Desktop, a LangChain agent with MCP support) is pointed at the EVIKAP MCP endpoint,  
**Then:**
- The agent discovers the `evikap_query` tool from the tool manifest without any EVIKAP-specific configuration beyond the MCP endpoint URL and an API key.
- The agent can invoke `evikap_query(query: str, requester_identity: str) -> QueryResponse` successfully.
- The response matches the same typed `QueryResponse` schema as the human-facing API.
- The MCP gateway applies the same permission and guardrail controls as the internal API.
- The acceptance check is documented: a reference agent integration test passes end-to-end without EVIKAP-specific client code.

---

## Functional Requirements

- FR-010 (Standards-based machine agent interface).

---

## Non-Functional Requirements

- NFR-002 (Security) — the MCP gateway applies the same authentication (JWT or MCP-standard API key) and permission filter as the internal API. No bypass possible via the MCP route.
- NFR-010 (Maintainability) — the MCP gateway is a thin adapter over the existing `/api/v1/query` endpoint; it does not duplicate query logic.
- NFR-006 (Performance) — MCP gateway adds ≤50ms overhead (it is a pure protocol translation layer, no heavy computation).

---

## Dependencies

- US-011 (API query endpoint — the gateway wraps this).
- US-014/US-016/US-017 (Permission enforcement and auth — applied equally to MCP consumers).
- US-028 (OTel tracing — MCP gateway calls are traced with the same `trace_id` mechanism).

---

## Assumptions

- MCP version: the current stable Model Context Protocol specification (as of PI-3 start date).
- The MCP gateway is implemented as a new FastAPI router in the backend service (not a separate service).
- MCP authentication: an API key header (`X-API-Key`) issued to the agent consumer; mapped to a service identity in the `users` table (not a human user).
- Rate limiting is applied at the MCP gateway level (separate rate limit pool from human users).

---

## Edge Cases

- **MCP client sends a malformed tool invocation:** Return an MCP-standard error response; do not expose internal error details.
- **MCP client sends a `requester_identity` that does not match the authenticated API key:** Reject with HTTP 403; the identity must be tied to the API key, not caller-supplied.
- **MCP tool manifest version changes (MCP spec updates):** Version the gateway endpoint (`/mcp/v1/`) to allow backward compatibility.

---

## Technical Notes / Implementation Considerations

- **Tool manifest endpoint:** `GET /mcp/v1/tools` — returns:
  ```json
  {
    "tools": [{
      "name": "evikap_query",
      "description": "Query EVIKAP's enterprise knowledge base with a natural language question. Returns a cited answer drawn from indexed sources.",
      "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}}, "required": ["query"]}
    }]
  }
  ```
- **Tool invocation endpoint:** `POST /mcp/v1/tools/evikap_query` — translates MCP request to internal `POST /api/v1/query` call; translates response back to MCP format.
- **Auth:** `X-API-Key` header → looked up in a `service_api_keys` table; mapped to a `user_id` (service identity); the same JWT-based permission filter is applied using the service identity.
- **Reference integration test:** A pytest test using a simple MCP client library; asserts the tool is discoverable and invocable end-to-end.

---

## Definition of Done

- [ ] `GET /mcp/v1/tools` endpoint returns a valid tool manifest.
- [ ] `POST /mcp/v1/tools/evikap_query` translates MCP invocations to internal query calls.
- [ ] API key authentication and service identity permission filter applied.
- [ ] Rate limiting applied at MCP gateway level.
- [ ] Reference integration test passes end-to-end (no EVIKAP-specific client code).
- [ ] MCP gateway adds ≤50ms median overhead confirmed.
- [ ] OTel spans include `mcp.tool_name` attribute for gateway requests.
- [ ] CI passes.

---

## Priority

**High** in PI-3 (core PI-3 objective per PI planning).

## Estimated Effort

**M (Medium)** — ~3–5 days (tool manifest, adapter endpoint, API key auth, rate limiting, integration test).

## Related Epics / Features

- FEAT-10 (MCP-based agent tool interface)
- FR-010
- NFR-002 (Security)
