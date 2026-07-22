# VigilRAG — Governance-Gated Enterprise Agentic RAG Platform

[![License: PolyForm Shield 1.0.0](https://img.shields.io/badge/License-PolyForm%20Shield%201.0.0-purple.svg)](LICENSE)
[![CI](https://github.com/mittalpk/VigilRAG/actions/workflows/ci.yml/badge.svg)](https://github.com/mittalpk/VigilRAG/actions/workflows/ci.yml)

A **cloud-native knowledge retrieval platform** that unifies enterprise data sources — code repositories, policy documents, databases, and wikis — into a single, traceable, LLM-ready API.

## Overview

VigilRAG addresses a core enterprise challenge: **knowledge is scattered across disconnected systems**. Employees and AI agents alike waste time context-switching between GitHub, Confluence, databases, and documentation portals — or worse, AI agents get broad, ungoverned access to those systems because no safe unified interface exists. VigilRAG's target design provides a unified retrieval layer and a governed multi-agent reasoning engine on top of it, with a hard trust boundary between reasoning and data access.

## Project Status

| Area | Current state | Target state |
|---|---|---|
| Retrieval | Keyword/filename matching over GitHub and Azure Blob content | Hybrid semantic + keyword retrieval with citations |
| Agent reasoning | Single-pass plan → execute → respond | Genuinely iterative, evidence-driven refinement, bounded by `max_iterations` |
| Database source | Not implemented (filename search only) | Real Postgres + pgvector data layer |
| Trust boundary (agent ↔ data) | **Implemented and enforced** — the agent service holds no source-system credentials | Unchanged — this is a preserved architectural strength |
| CI/CD | Test/build validation gate on push and PR (no auto-deploy) | Same, plus an automated LLM-evaluation quality gate |
| Access control | Single hardcoded admin, JWT auth | RBAC, multi-user |

This table is a summary — the full, unvarnished technical audit is in [`knowledge/VigilRAG_AUDIT.md`](knowledge/VigilRAG_AUDIT.md), and the plan to close every gap above is in [`knowledge/08-roadmap/`](knowledge/08-roadmap/).

---

## Architecture

The platform is structured as a **4-layer cloud-native system**:

### Layer 1 — Data Sources
Live enterprise systems: **GitHub** (code), **Azure Blob Storage** (policy docs, wikis), **SQL Databases** (schemas, operational state — roadmap, see status table above), **Confluence** (internal documentation, demo-mode local fallback today).

### Layer 2 — Knowledge API (Retrieval)
The `POST /api/v1/knowledge/query` endpoint is the **single source-of-truth interface**. It:
- **Abstracts source complexity**: GitHub and Azure Blob behind a single API contract.
- **Enforces a trust boundary**: all retrieval is read-only; the agent tier never touches source-system credentials directly — this is the one architectural claim in this README that is fully implemented and verifiable in code today.
- **Returns structured, traceable JSON**: responses include normalized `facts` with `stable_id`, `timestamp`, and `source_url`.

### Layer 3 — Agent Orchestrator
Built on **LangGraph + Gemini**, this layer runs a `plan → execute → respond` flow today (single pass). Genuine iterative refinement — re-planning when evidence is insufficient, bounded by a real `max_iterations` — is scoped as [FEAT-04](knowledge/06-agile-delivery/PROGRAM_BACKLOG.md) and not yet implemented; see [Project Status](#project-status).

### Layer 4 — Application Layer
A **React 18 + TypeScript** dashboard served via **Nginx**, with direct API integration.

---

## Technical Stack

| Layer         | Technology                              | Role |
|---------------|------------------------------------------|------|
| Frontend      | React 18, TypeScript, Vite, Nginx        | Interactive knowledge dashboard |
| Backend API   | Python 3.12, FastAPI, Pydantic           | API gateway + retrieval aggregator |
| Agent Service | LangGraph, Gemini 2.5 Flash / Pro         | Multi-step reasoning engine |
| Auth          | Python-JWT + shared internal API key      | Token-based & service-key security boundary |
| Infrastructure| Terraform, Azure Container Apps (enterprise profile) or Netlify + Koyeb + Supabase (demo profile) | See [Deployment](#deployment) |

---

## Documentation

All project documentation lives in **[`knowledge/`](knowledge/)** — the enterprise solution-architecture knowledge base: problem statement, the honest [current-state audit](knowledge/VigilRAG_AUDIT.md), TOGAF architecture vision/business/data/application/technology views (including the [as-built system architecture](knowledge/04-solution-architecture/ARCHITECTURE.md) and the two deployment runbooks referenced below), BABOK requirements specs, Lean product-fit validation plan, SAFe epic/backlog/PI plan, governance/risk register, and a concrete execution runbook + issue log. Start at [`knowledge/README.md`](knowledge/README.md).

---

## Quick Start (Local)

```bash
# 1. Configure environment variables
cp .env.example .env

# 2. Start all services
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend Dashboard | `http://localhost:5173` |
| Backend API (Swagger) | `http://localhost:8000/docs` |
| Agent Service | `http://localhost:8001/docs` |

## Testing

```bash
python3 -m pytest backend/tests agent/tests -v   # backend + agent
cd frontend && npm ci && npm run build            # frontend type-check + build
```

The same commands run in CI on every push and pull request to `main` — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml). CI validates and gates; it does not deploy.

## Deployment

Two deployment profiles exist, documented in [`knowledge/04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md §6`](knowledge/04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6-deployment-profiles):

| Profile | Stack | Use case | Runbook |
|---|---|---|---|
| Enterprise | Azure Container Apps + Terraform, managed Postgres/Redis/Key Vault | A real pilot deployment meeting the project's non-functional requirements | [`knowledge/04-solution-architecture/deployment/AZURE_DEPLOYMENT.md`](knowledge/04-solution-architecture/deployment/AZURE_DEPLOYMENT.md) |
| Demo | Netlify (frontend) + Koyeb (backend/agent, free tier) + Supabase (Postgres) | Low-cost public demo hosting; **not** representative of production scale, availability, or security posture | [`knowledge/04-solution-architecture/deployment/deployment_plan.md`](knowledge/04-solution-architecture/deployment/deployment_plan.md) |

Neither profile is wired to automatic deployment from this repository's CI — deployment is a deliberate, manual action following the linked runbook.

## Contributing

Issues and PRs are welcome; see [`knowledge/07-governance-risk/ARCHITECTURE_GOVERNANCE.md`](knowledge/07-governance-risk/ARCHITECTURE_GOVERNANCE.md) for the change-control process any architecture-significant contribution goes through.

## License

PolyForm Shield License 1.0.0 — see [LICENSE](LICENSE).


