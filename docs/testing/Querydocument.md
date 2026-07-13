# Omega Nexus — Platform Validation Queries

This document provides a set of **functional validation queries** covering both the Knowledge API (Layer 2) and the Multi-Agent Orchestrator (Layer 3). Use these to verify end-to-end connectivity, data retrieval accuracy, and agent reasoning quality.

---

## 1. Cloud Documentation Sourcing (Knowledge API → Azure Blob Storage)

*Validates the platform's ability to retrieve and parse policy documents from the Azure Blob Wiki Container (`omega-wiki`).*

### Query 1.1: Data Privacy & Classification
> **Query:** "What is our official data classification model, and under what tier does our PII fall?"
>
> **Expected Result:** Returns facts from `Data_Privacy_Policy.md` identifying classification tiers (Public, Internal, Restricted) and confirming PII is classified as Restricted, requiring AES-256 encryption at rest.
>
> **Validates:** Azure Blob retrieval, policy document parsing, structured fact extraction.

### Query 1.2: Deployment Policy & GitOps
> **Query:** "Can developers push code directly to the main branch? What is our CI/CD policy for deployments?"
>
> **Expected Result:** Sources `Deployment_CI_CD.md`, returning facts confirming that direct pushes to `main` are blocked; all deployments require an approved Pull Request and passing automated test suite.
>
> **Validates:** Policy retrieval, boolean fact extraction, metadata traceability.

---

## 2. Live Code Sourcing (Knowledge API → GitHub API)

*Validates the platform's real-time GitHub Search API integration and recursive code tree traversal.*

### Query 2.1: Cryptographic Utilities
> **Query:** "How does the omega-core utilities package generate stable IDs? Show me the cryptographic hashing logic."
>
> **Expected Result:** Sources `omega-core/utils/crypto.py` and extracts the `generate_stable_id()` function using `hashlib.sha256`. Returns the function body as a traceable fact with a GitHub commit SHA as the stable ID.
>
> **Validates:** GitHub Search API, code file retrieval, stable ID generation.

### Query 2.2: Authentication Model
> **Query:** "Which service is responsible for providing the `validate_token` dependency, and how is it structured?"
>
> **Expected Result:** Sources `omega-auth/models.py`, returning the structure of the `OmegaUser` Pydantic model and the `validate_token` FastAPI dependency.
>
> **Validates:** Cross-repository search, code structure extraction, metadata attribution.

---

## 3. Multi-Source Reasoning (Multi-Agent Orchestrator → LangGraph)

*Validates complex, multi-step queries that require the agent to plan, retrieve from multiple sources, and synthesize a grounded conclusion.*

### Query 3.1: Implementation-to-Policy Compliance Trace
> **Query:** "Trace the implementation of the root checkout endpoint in the `payment-service`. Does its API structure comply with our official API Authentication Policy guidelines?"
>
> **Expected Agent Workflow:**
> 1. **Plan**: Identifies two tool calls needed — one to Azure (policy), one to GitHub (code).
> 2. **Execute**: Retrieves `API_Authentication_Policy.md` from Azure Blob Storage.
> 3. **Execute**: Retrieves `payment-service/main.py` from GitHub.
> 4. **Respond**: Synthesizes a compliance verdict — confirms whether the checkout endpoint uses the required `validate_token` OAuth2 dependency.
>
> **Validates:** Multi-step planning, cross-source evidence gathering, policy-vs-implementation synthesis.

### Query 3.2: Database Architecture Compliance
> **Query:** "According to our Architecture Guidelines, what kind of databases are we allowed to use for operational state? And based on the current schemas, is our user table following that rule?"
>
> > [!IMPORTANT]
> > **Phase 1 Remediation Note**: The simulated database schema fallback (which previously fabricated a `CREATE TABLE users` response when the query mentioned "user/schema") has been completely removed to prevent data fabrication. As a result, this query will evaluate to "no matching schema found in configured sources" unless a real `schema.sql` file exists in the targeted repository.
>
> **Expected Agent Workflow:**
> 1. **Plan**: Identifies two tool calls — architecture policy (Azure) + database schema (SQL/GitHub).
> 2. **Execute**: Retrieves architectural database guidelines from `Architecture_Guidelines.md`.
> 3. **Execute**: Retrieves schema definition from `schema.sql` or auth model metadata (returns empty if not present).
> 4. **Respond**: Synthesizes a compliance summary based on the actual retrieved schemas.
>
> **Validates:** Agent state management across iterations, hybrid source synthesis, compliance-grade output.

### Query 3.3: Production Logging Compliance
> **Query:** "Check our `Logging_Policy.md` in Azure and compare it with the `payment-service` implementation in GitHub. Are we using the correct log levels for PII data?"
>
> **Expected Agent Workflow:**
> 1. Retrieves global logging standards from Azure.
> 2. Scans `payment-service` for logger configurations.
> 3. Identifies any "Data Leakage" risks where PII might be logged at `INFO` instead of `DEBUG`.
>
> **Validates:** Qualitative policy-to-code auditing.

### Query 3.4: Cryptographic Standard Enforcement
> **Query:** "Verify if the `auth-service` uses the global standard `AES-256` encryption as per our security policy. If not, identify the current implementation."
>
> **Expected Agent Workflow:**
> 1. Finds the specific encryption requirement in `Security_Policy.md`.
> 2. Searches the `auth-service` for cryptographic libraries and constants.
> 3. Flags discrepancies (e.g., if code uses `AES-128` or `DES`).
>
> **Validates:** Technical security compliance auditing.

---

## 4. Developer Onboarding & Discovery (Nexus Knowledge Search)

*Queries focused on accelerating developer velocity by treating the codebase and documentation as a searchable intelligence graph.*

### Query 4.1: "Gold Standard" Implementation Template
> **Query:** "I need to add a new endpoint to the `user-service`. Based on existing repositories and our 'API Identity Guidelines', show me an example of a correctly structured FastAPI endpoint with OAuth2 protection."
>
> **Expected Result:** Pulls the identity rule from Azure and the most "compliant" code snippet from GitHub (e.g., from `payment-service`), providing a ready-to-use template.
>
> **Validates:** Pattern matching across docs and code.

### Query 4.2: Infrastructure Secret Management
> **Query:** "What are the required environment variables for deploying a new microservice in the Omega Nexus ecosystem, according to our Cloud Deployment policy and existing `docker-compose` examples?"
>
> **Expected Result:** Cross-references `Cloud_Deployment.md` with the `docker-compose.yml` file, listing required keys (e.g., `AZURE_CLIENT_ID`, `GITHUB_PAT`) and explaining why they are mandatory.
>
> **Validates:** Infrastructure-as-Code (IaC) discovery and configuration auditing.

---

---

## 5. Advanced Architectural Analysis & Impact Assessment (Nexus Level 3)

*Queries demonstrating the platform's ability to reason across the entire ecosystem, identifying dependencies, risks, and architectural drift.*

### Query 5.1: Cross-Service Impact Assessment
> **Query:** "If we change the `OmegaUser` Pydantic model in `omega-auth`, which services in our GitHub ecosystem will be affected? Trace all dependencies."
>
> **Expected Agent Workflow:**
> 1. Identifies the model in `omega-auth`.
> 2. Searches all repositories for imports or references to `OmegaUser`.
> 3. Summarizes the "Blast Radius" of the proposed change.
>
> **Validates:** Global dependency tracing and impact assessment.

### Query 5.2: Architectural Alignment (Database Isolation)
> **Query:** "Our 'Microservices Guideline' in Azure prohibits services from sharing the same database schema. Check the `payment-service` and `user-service` configurations to ensure they are isolated."
>
> **Expected Agent Workflow:**
> 1. Retrieves the isolation rule from `Microservices_Guideline.md`.
> 2. Inspects `docker-compose.yml` and environment variables for both services.
> 3. Flags any "Shared Database" anti-patterns.
>
> **Validates:** Multi-service architectural auditing.

### Query 5.3: Security Hardening (Secret Management)
> **Query:** "Identify any hardcoded credentials or lack of 'Secret Store' integration in our current configurations, and cross-reference with our 'Secret Management Policy' in Azure."
>
> **Expected Agent Workflow:**
> 1. Reads the `Secret_Management_Policy.md`.
> 2. Scans `.env`, `docker-compose.yml`, and `main.py` files for plain-text secrets or keys.
> 3. Recommends migration to Azure Key Vault where missing.
>
> **Validates:** Automated security oversight and remediation discovery.

### Query 5.4: Service Reliability (Observability Standard)
> **Query:** "Based on our 'Service Reliability Policy', do our current FastAPI services implement the required `/health` and `/ready` endpoints consistently?"
>
> **Expected Agent Workflow:**
> 1. Checks the reliability requirement in Azure docs.
> 2. Scans all active FastAPI `main.py` routers for health probe implementations.
> 3. Identifies services that are "Dark" (missing observability).
>
> **Validates:** Reliability and SRE-level compliance auditing.

---

## How to Run Validation

1. Open the dashboard at **`http://localhost:5173`**.
2. For Queries 1.x and 2.x → Use the **Knowledge API** tab.
3. For Queries 3.x → Use the **Multi-Agent Orchestrator** tab.
4. Verify the **Traceable Metadata** section in each response: source system, stable ID, and timestamp must be present for all returned facts.
