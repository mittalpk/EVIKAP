# Omega Nexus Architecture

Omega Nexus is a **cloud-native knowledge retrieval platform** built on a strict 4-layer separation of concerns. Each layer has a well-defined role, a clear trust boundary, and can be independently scaled or replaced.

---

## Architectural Overview

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Application Layer (React UI / API Consumers)  │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Agent Orchestration (LangGraph State Machine) │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Knowledge API  (Unified Semantic Retrieval)   │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Data Sources (GitHub, Azure Blob, SQL, Wiki)  │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Data Sources

The raw enterprise data layer. Omega Nexus is designed for extensibility — new sources can be added without changing higher layers.

| Source | Content Type | Access Method |
|---|---|---|
| GitHub | Source code, configs | GitHub Search API + Recursive Tree |
| Azure Blob Storage | Policy docs, wikis | Azure SDK + SAS / Managed Identity |
| SQL Databases | Schemas, operational state | SQLAlchemy |
| Confluence (planned) | Internal documentation | REST API |

---

## Layer 2 — Knowledge API (`backend/`)

The Knowledge API is the **single source of truth interface**. It is a stateless, read-only retrieval layer that abstracts all data source complexity behind a single REST contract.

### Design Principles
- **Source Abstraction**: Consumers never know whether a fact came from GitHub, Azure, or a database.
- **Trust Boundary**: Enforces safe, read-only, validated access — the Agent layer never directly touches raw data sources.
- **Structured Data Contracts**: Every response returns a normalized JSON schema:
  - `facts[]` — extracted knowledge with confidence scores
  - `metadata[]` — source system, stable ID, URL, and ISO timestamp for full traceability
- **LLM Role**: Gemini is used once per request to translate natural language into structured API filters (semantic-to-query translation). This is intentionally stateless.

### Key Technologies
- **FastAPI (Python 3.12)**: ASGI framework with automatic OpenAPI/Swagger documentation.
- **Python-JWT & Shared Key Auth**: Every request must carry a valid JWT (for user sessions) or a shared `X-Internal-API-Key` (for service-to-service agent calls), verified with constant-time comparisons.
- **Pydantic**: Strict environment variable validation on startup via `config.py`.

### Core Files
- `backend/app/main.py` — ASGI entry point; registers CORS, auth, and routers.
- `backend/app/routers/knowledge.py` — Primary retrieval logic: hybrid search across GitHub, Azure, and SQL.
- `backend/app/config.py` — Environment-validated configuration (Client IDs, Storage URIs, DB URLs).

---

## Layer 3 — Agent Orchestration (`agent/`)

The Agent Service is a dedicated microservice for **stateful multi-step reasoning**. It treats the Knowledge API as a tool and never accesses data sources directly.

### Design Principles
- **Stateful Orchestration**: LangGraph maintains a `StateGraph` object across nodes — enabling iterative refinement if initial retrieval is insufficient.
- **Workflow Control**: The agent autonomously decides when to call tools, how many times, and when evidence is sufficient to generate a response.
- **Grounded Synthesis**: The final response node (Respond) synthesizes only retrieved facts — it does not hallucinate or generate information beyond what the Knowledge API returned.

### LangGraph Execution Nodes

| Node | LLM Used | Responsibility |
|---|---|---|
| `node_plan` | ✅ Yes | Decomposes the user task into a sequence of tool calls |
| `node_execute` | ❌ No | Dispatches tool calls to the Knowledge API |
| `node_respond` | ✅ Yes | Synthesizes all gathered evidence into a traceable conclusion |

### Key Technologies
- **LangGraph**: Models the agent as a cyclical `StateGraph`. Supports conditional edges for iterative loops.
- **Gemini 1.5 Pro**: Powers the Plan and Respond nodes via the Google AI SDK.

### Core Files
- `agent/app/graph.py` — The LangGraph state machine definition.
- `agent/app/tools.py` — Tool definitions that wrap Knowledge API endpoints. Enforces the trust boundary.
- `agent/app/main.py` — FastAPI entry point for the agent service. Includes CORS for frontend access.

---

## Layer 4 — Application Layer (`frontend/`)

The frontend is a **React 18 + TypeScript** Single Page Application (SPA) served via Nginx.

### Key Technologies
- **React 18 + TypeScript**: Strongly-typed, component-based UI.
- **Vite**: Fast build tooling with Hot Module Replacement (HMR) for development.
- **Nginx**: Production web server. Also acts as a reverse proxy, routing `/api/*` requests to the Backend service to eliminate CORS issues.

### Core Files
- `frontend/src/App.tsx` — Main dashboard: Knowledge API tab and Multi-Agent Orchestrator tab with embedded architecture documentation.
- `frontend/src/api/client.ts` — Typed API client bridging the UI to backend services.
- `frontend/nginx.conf` — SPA routing and reverse proxy configuration.

---

## Request Lifecycle

```
User (Browser)
   │
   ▼
Nginx (frontend:80)
   │  Reverse proxy /api/* calls
   ▼
FastAPI Backend (backend:8000)
   │  Validates OAuth 2.0 JWT
   │  For /knowledge → runs hybrid search (GitHub + Azure + SQL)
   │  For /agent    → proxies to Agent service
   ▼
LangGraph Agent (agent:8001)        [for multi-step tasks]
   │  Runs plan → execute → respond state machine
   │  Calls back to Knowledge API (backend) as a tool
   ▼
Knowledge API (backend:8000)        [as a tool, called by agent]
   │  Returns structured JSON facts + metadata
   ▼
Response flows back through Backend → Nginx → Browser
```

---

## Infrastructure (`terraform/`)

Managed via **Terraform** (Infrastructure-as-Code) targeting **Microsoft Azure**.

| Resource | Purpose |
|---|---|
| Azure Container Registry (ACR) | Private Docker image registry (`omegaregistry`) |
| Azure Container Apps (ACA) | Serverless runtime for backend and agent services |
| Virtual Network + NSGs | Virtual network for container isolation (planned/partial) |
| Log Analytics Workspace | Centralized observability |
