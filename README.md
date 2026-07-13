# Omega Nexus — Unified Knowledge & Reasoning Platform

A **cloud-native knowledge retrieval platform** that unifies enterprise data sources — code repositories, policy documents, databases, and wikis — into a single, traceable, LLM-ready API.

## Overview

Omega Nexus addresses a core enterprise challenge: **knowledge is scattered across disconnected systems**. Developers waste time context-switching between GitHub, Confluence, databases, and documentation portals. Omega Nexus solves this by providing a unified semantic retrieval layer and an intelligent multi-agent reasoning engine on top of it.

---

## Architecture

The platform is structured as a **4-layer cloud-native system**:

### Layer 1 — Data Sources
Live enterprise systems: **GitHub** (code), **Azure Blob Storage** (policy docs, wikis), **SQL Databases** (schemas, operational state), **Confluence** (internal documentation).

### Layer 2 — Knowledge API (Unified Semantic Retrieval)
The `POST /api/v1/knowledge/query` endpoint is the **single source of truth interface**. It:
- **Abstracts source complexity**: GitHub, Azure Blob, and SQL behind a single API contract.
- **Enforces a trust boundary**: All retrieval is read-only and validated — no agent ever touches raw sources directly.
- **Returns structured, traceable JSON**: Every response includes normalized `facts` with `stable_id`, `timestamp`, and `source_url` — enabling downstream compliance auditing and LLM-safe consumption.

### Layer 3 — Multi-Agent Orchestrator (Stateful Reasoning)
Built on **LangGraph + Gemini**, this layer decomposes complex, multi-source queries into a stateful execution plan:
- `Plan` → `Execute` (tool calls to Knowledge API) → `Respond` (synthesized conclusion)
- Iterates until sufficient evidence is gathered. Never fabricates facts beyond what is retrieved.

### Layer 4 — Application Layer
A **React 18 + TypeScript** dashboard served via **Nginx**, with direct API integration and an embedded documentation hub explaining the system architecture.

---

## Technical Stack

| Layer         | Technology                              | Role |
|---------------|-----------------------------------------|------|
| Frontend      | React 18, TypeScript, Vite, Nginx       | Interactive knowledge dashboard |
| Backend API   | Python 3.12, FastAPI, Pydantic          | API gateway + Unified retrieval aggregator |
| Agent Service | LangGraph, Gemini 2.5 Flash             | Stateful multi-step reasoning engine |
| Auth          | Python-JWT + Shared API Key             | Token-based & Service key security boundary |
| Infrastructure| Terraform, Azure Container Apps         | Serverless cloud deployment |

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

## Cloud Deployment

See [AZURE_DEPLOYMENT.md](./docs/deployment/AZURE_DEPLOYMENT.md) for deploying to **Azure Container Apps** via Terraform (Infrastructure-as-Code).
