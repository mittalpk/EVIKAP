# VigilRAG Deployment Plan: Netlify, Koyeb, and Supabase

This document outlines the detailed step-by-step implementation plan for hosting VigilRAG using the free tier of Netlify, Koyeb, and Supabase.

---

## 1. Architectural Mapping

```
┌──────────────────────────────────────────────────────────┐
│              User Browser (Custom Domain)               │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼ HTTPS
┌──────────────────────────────────────────────────────────┐
│        Frontend: Netlify (Static React Hosting)          │
│               [vigilrag.yourdomain.com]                │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼ REST / WebSockets (HTTPS)
┌──────────────────────────────────────────────────────────┐
│      FastAPI Backend: Koyeb (Containerized Service)      │
│             [api-vigilrag.yourdomain.com]              │
└──────────────┬────────────────────────────┬──────────────┘
               │                            │
               │ Internal / Public          │ SQL / Postgres
               ▼                            ▼
┌──────────────────────────────┐    ┌──────────────────────┐
│  LangGraph Agent: Koyeb      │    │ Database: Supabase   │
│  [agent-vigilrag...]       │    │ [db.supabase.co]     │
└──────────────────────────────┘    └──────────────────────┘
```

---

## 2. Platform Requirements & Setup

### Database (Supabase)
1. Sign up on [Supabase](https://supabase.com/).
2. Create a new project named `vigilrag`.
3. Locate the **Database Connection String** in `Project Settings -> Database`. 
4. Select the **URI** connection type (e.g. `postgresql://postgres:[YOUR-PASSWORD]@db.[REF].supabase.co:5432/postgres`) and save it.

### Frontend (Netlify)
1. Sign up on [Netlify](https://netlify.com/) and connect your GitHub account.
2. Select `Import from Git` and choose the `mittalpk/VigilRAG` repository.
3. Configure the build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
4. Set up Environment Variables:
   - `VITE_BACKEND_URL`: URL of the Koyeb Backend API (e.g., `https://api-vigilrag.yourdomain.com`).
   - `VITE_AGENT_URL`: URL of the Koyeb Agent Service (e.g., `https://agent-vigilrag.yourdomain.com`).

### Backend & Agent (Koyeb)
Because Koyeb provides one free Nano instance (512MB RAM) per account, you have two deployment pathways for running both the Backend and the Agent:
- **Option A (Split Accounts / Hobby)**: Set up one service on your account and another on a second free account.
- **Option B (Combined Container - Recommended for single free tier)**: Package both FastAPI applications into a single Docker container using a supervisor process (like `supervisord` or a simple bash entrypoint script) running on different ports within the same Koyeb App.

For the standard multi-service layout (Option A), configure the following in Koyeb:

#### Service 1: `vigilrag-backend`
- **Source**: GitHub repository `mittalpk/VigilRAG`
- **Builder**: Dockerfile (Path: `backend/Dockerfile`)
- **Port**: `8000`
- **Environment Variables**:
  - `DATABASE_URL`: Your Supabase connection string.
  - `AGENT_SERVICE_URL`: URL of the Koyeb Agent Service.
  - `ALLOWED_ORIGINS`: `["https://vigilrag.yourdomain.com", "http://localhost:5173"]`
  - `INTERNAL_API_KEY`: A secure 32-byte API key.
  - `SECRET_KEY`: A secure 32-byte JWT signing key.
  - `ADMIN_USERNAME`: `admin`
  - `ADMIN_PASSWORD`: A secure admin password.

#### Service 2: `vigilrag-agent`
- **Source**: GitHub repository `mittalpk/VigilRAG`
- **Builder**: Dockerfile (Path: `agent/Dockerfile`)
- **Port**: `8000` (mapped externally as needed)
- **Environment Variables**:
  - `INTERNAL_API_KEY`: Must match the backend's `INTERNAL_API_KEY`.
  - `BACKEND_URL`: URL of the Koyeb Backend Service.
  - `GEMINI_API_KEY`: Your Google Gemini API Key.
  - `ALLOWED_ORIGINS`: `["https://vigilrag.yourdomain.com", "http://localhost:5173"]`

---

## 3. DNS & Domain Configuration

Configure the following CNAME/A records in your DNS provider:

| Host / Subdomain | Type | Target / Value | Purpose |
| :--- | :--- | :--- | :--- |
| `vigilrag` | CNAME | `[your-netlify-app-name].netlify.app` | React Frontend Entry Point |
| `api-vigilrag` | CNAME | `[your-koyeb-backend-app-name].koyeb.app` | Backend API Layer |
| `agent-vigilrag` | CNAME | `[your-koyeb-agent-app-name].koyeb.app` | LangGraph Agent Gateway |

---

## 4. Verification Checklists

### 1. Database Connection
Run a test script or check backend logs to verify that SQLAlchemy can connect to the Supabase PostgreSQL cluster:
```python
# Check backend startup log
"✓ Settings initialized: DATABASE_URL loaded"
```

### 2. CORS and Options Preflight
Execute a curl request simulating a preflight check from the Netlify domain:
```bash
curl -I -X OPTIONS \
  -H "Origin: https://vigilrag.yourdomain.com" \
  -H "Access-Control-Request-Method: POST" \
  https://api-vigilrag.yourdomain.com/api/v1/knowledge/query
```
**Expected Response**: `HTTP/1.1 200 OK` with header `Access-Control-Allow-Origin: https://vigilrag.yourdomain.com`.

### 3. Startup Verification
Verify that both Koyeb services start up successfully without triggering the startup security guards. If the environment variables are not correctly configured, Koyeb logs will show:
`RuntimeError: INTERNAL_API_KEY is not configured or uses insecure default — refusing to start`
Ensure the logs show successful initialization.
