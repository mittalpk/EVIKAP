# Azure Live Deployment Guide — Omega TechStack

This guide takes the `Omega_TechStack` from zero to fully live on Azure, step by step.

---

## Prerequisites

Install all required tools first:

```bash
# 1. Azure CLI  
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az --version  # confirm ≥ 2.58

# 2. Terraform
sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
terraform --version  # confirm ≥ 1.7

# 3. Docker
curl -fsSL https://get.docker.com | sh
docker --version

# 4. Node.js (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## Phase 1 — Azure Account Setup

### 1.1 Log into Azure

```bash
az login
# A browser window opens. Sign in with your Omega Azure account.

# List available subscriptions
az account list --output table

# Set the correct subscription
az account set --subscription "<your-subscription-id>"
az account show  # confirm correct subscription is active
```

### 1.2 Register Required Providers

```bash
az provider register --namespace Microsoft.ContainerInstance
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Network

# Wait for all to be Registered (status check)
az provider show -n Microsoft.App --query registrationState
```

---

## Phase 2 — Entra ID (Azure AD) App Registration

This secures every API endpoint with real bearer tokens.

### 2.1 Register the Application

```bash
# Create the App Registration
APP=$(az ad app create \
  --display-name "omega-nexus-api" \
  --sign-in-audience AzureADMyOrg \
  --query "{appId: appId, objectId: id}" \
  --output json)

CLIENT_ID=$(echo $APP | python3 -c "import sys,json; print(json.load(sys.stdin)['appId'])")
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "AZURE_CLIENT_ID=$CLIENT_ID"
echo "AZURE_TENANT_ID=$TENANT_ID"
```

### 2.2 Expose an API Scope

```bash
# Set the Application ID URI
az ad app update \
  --id $CLIENT_ID \
  --identifier-uris "api://$CLIENT_ID"

# Add the user_impersonation scope via the portal (required for interactive users):
# Azure Portal → Entra ID → App Registrations → omega-nexus-api
# → Expose an API → Add a scope
# Name: user_impersonation
# Admin consent display name: "Access Omega Nexus API"
# State: Enabled
```

### 2.3 Create a Client Secret (for service-to-service auth)

```bash
SECRET=$(az ad app credential reset \
  --id $CLIENT_ID \
  --display-name "nexus-backend-secret" \
  --years 1 \
  --query password \
  --output tsv)

echo "AZURE_CLIENT_SECRET=$SECRET"
# Store this securely — it won't be shown again.
```


## Phase 2.1 — Configure Your Local Secrets

To keep your deployment secure and avoid typing passwords manually, set these environment variables in your terminal:

```bash
# GitHub Credentials (no secrets needed here!)
export TF_VAR_github_username="<your-github-username>"
export TF_VAR_github_repo_owner="<your-github-username>"

# Azure Service Principal (from Phase 9.1)
export TENANT_ID="<your-tenant-id>"
export CLIENT_ID="<your-client-id>"
```

---

## Phase 3 — Provision Infrastructure with Terraform

```bash
cd /path/to/OmegaNexus/terraform

# Initialize Terraform providers
terraform init

# Preview what will be created  
terraform plan \
  -var="azure_tenant_id=$TENANT_ID" \
  -var="azure_client_id=$CLIENT_ID"

# 3.2 Apply (this takes ~5-10 minutes)
# This will create the Key Vault and secret "slots".
terraform apply \
  -var="azure_tenant_id=$TENANT_ID" \
  -var="azure_client_id=$CLIENT_ID" \
  -var="github_username=$TF_VAR_github_username" \
  -var="github_repo_owner=$TF_VAR_github_repo_owner" \
  -auto-approve

# 3.3 UPDATE SECRETS IN PORTAL
# 1. log into Azure Portal -> Key Vault -> 'kv-omega-nexus-*'
# 2. Go to 'Objects' -> 'Secrets'
# 3. Click 'gemini-api-key' -> 'New Version' -> Add your Gemini Key -> Create
# 4. Click 'github-pat' -> 'New Version' -> Add your GitHub PAT -> Create

# Save outputs
BACKEND_URL=$(terraform output -raw backend_url)

echo "Backend: $BACKEND_URL"
```

**What gets created:**
| Resource | Name | Purpose |
|---|---|---|
| Resource Group | `rg-omega-nexus` | Container for all resources |
| Key Vault | `kv-omega-nexus-*` | **Secure secret storage (Zero-Input)** |
| Virtual Network | `vnet-omega-nexus` | Network isolation |
| ACI Subnet | `snet-aci` | Sandboxed execution |
| Network Security Group | `nsg-aci-sandboxes` | Block internet egress |
| Container Registry | **GHCR** | GitHub-hosted private images (Free) |
| Container App Env | `cae-omega-nexus` | Managed hosting |
| Container App | `ca-omega-backend` | Managed Identity + KV Access |
| Container App | `ca-omega-agent` | Managed Identity + KV Access |
| Container App | `ca-omega-frontend` | Managed Identity + KV Access |

---

## Phase 4 — Build and Push to GitHub Container Registry (GHCR)

```bash
cd /path/to/OmegaNexus

# 4.1 Create a GitHub PAT (Classic recommended)
# GitHub Fine-grained tokens currently have limited support for GHCR before the first push.
# 1. Go to GitHub Settings -> Developer Settings -> Personal access tokens -> Tokens (classic)
# 2. Click "Generate new token" (classic).
# 3. Select the following scopes:
#    - **write:packages** (to push images)
#    - **read:packages** (to pull images)
#    - **repo** (optional, but recommended for private repos)

# 4.2 Log into GHCR
echo <your-github-pat> | docker login ghcr.io -u <your-github-username> --password-stdin

# 4.3 Build and Push
# Replace <owner> with your GitHub username

# --- Backend ---
docker build -t ghcr.io/<owner>/omega-nexus-backend:latest ./backend
docker push ghcr.io/<owner>/omega-nexus-backend:latest

# --- Agent ---
docker build -t ghcr.io/<owner>/omega-nexus-agent:latest ./agent
docker push ghcr.io/<owner>/omega-nexus-agent:latest

# --- Frontend ---
docker build -t ghcr.io/<owner>/omega-nexus-frontend:latest ./frontend
docker push ghcr.io/<owner>/omega-nexus-frontend:latest
```

---

## Phase 5 — Configure Container App Secrets

The agent container needs the OpenAI API key injected securely via Azure Container App secrets (never hardcoded):

```bash
# Add OpenAI API key as a secret to the agent Container App
az containerapp secret set \
  --name ca-omega-agent \
  --resource-group rg-omega-nexus \
  --secrets "openai-api-key=<your-openai-api-key>"

# Set Backend environment variables
az containerapp update \
  --name ca-omega-backend \
  --resource-group rg-omega-nexus \
  --set-env-vars \
    AZURE_TENANT_ID=$TENANT_ID \
    AZURE_CLIENT_ID=$CLIENT_ID
```

---

## Phase 6 — Deploy Production Images via CI/CD

Now that your infrastructure is up (running "Hello World"), you can deploy the real OmegaNexus platform:

1.  **Push your code** to the `main` branch.
2.  The **GitHub Action** will build your real images and update the Container Apps.
3.  Verification: `https://ca-omega-backend.<location>.azurecontainerapps.io/health`

## Phase 7 — Verify Live Deployment

```bash
# Get the live backend URL
BACKEND_URL=$(az containerapp show \
  --name ca-omega-backend \
  --resource-group rg-omega-nexus \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Backend: https://$BACKEND_URL"

# Health check
curl https://$BACKEND_URL/health
# Expected: {"status": "healthy", "service": "omega-backend"}

# Check running revision status
az containerapp revision list \
  --name ca-omega-backend \
  --resource-group rg-omega-nexus \
  --output table
```

---

## Phase 8 — Enable Observability (OpenTelemetry → Azure Monitor)

```bash
# Add Application Insights
az monitor app-insights component create \
  --app omega-nexus-insights \
  --location westeurope \
  --resource-group rg-omega-nexus \
  --workspace law-omega-nexus

# Get connection string
APPINSIGHTS=$(az monitor app-insights component show \
  --app omega-nexus-insights \
  --resource-group rg-omega-nexus \
  --query connectionString -o tsv)

# Inject into backend container
az containerapp update \
  --name ca-omega-backend \
  --resource-group rg-omega-nexus \
  --set-env-vars APPLICATIONINSIGHTS_CONNECTION_STRING=$APPINSIGHTS
```

---

## Quick Reference — Environment File

Fill in your `.env` with all collected values:

```bash
AZURE_TENANT_ID=<from Phase 2.1>
AZURE_CLIENT_ID=<from Phase 2.1>
AZURE_SUBSCRIPTION_ID=<from Phase 1.1>
AZURE_RESOURCE_GROUP=rg-omega-nexus
AZURE_LOCATION=westeurope
OPENAI_API_KEY=sk-...
USE_ACI=true
DATABASE_URL=sqlite:///./omega.db
```

## Phase 7 — Troubleshooting State Sync Errors

If you see errors like **"already exists - to be managed via Terraform this resource needs to be imported"**, your local state is out of sync with Azure. Run these commands:

```bash
# Set your Subscription ID
SUB_ID="<your-azure-subscription-id>"

# Import the existing apps into Terraform State
terraform import azurerm_container_app.backend /subscriptions/$SUB_ID/resourceGroups/rg-omega-nexus/providers/Microsoft.App/containerApps/ca-omega-backend
terraform import azurerm_container_app.agent /subscriptions/$SUB_ID/resourceGroups/rg-omega-nexus/providers/Microsoft.App/containerApps/ca-omega-agent
terraform import azurerm_container_app.frontend /subscriptions/$SUB_ID/resourceGroups/rg-omega-nexus/providers/Microsoft.App/containerApps/ca-omega-frontend
```

Also, ensure **`TF_VAR_github_username`** is set in your terminal (Phase 2.1) to avoid registry configuration errors.

---

## Cost Estimates (westeurope, Absolute Zero Tier)

| Resource | Approximate Monthly Cost |
|---|---|
| Container App (Scale to Zero) | ~€0 - €10 (usage only) |
| Container Registry (GHCR) | **FREE** |
| Log Analytics (7 day retention) | ~€2 |
| Virtual Network | Free |
| **Total Estimate** | **~€2 - €12/month** |

> **Savings Tip**: By using GitHub Container Registry (GHCR) and scaling Container Apps to zero, your fixed monthly cost is nearly €0.

> Costs scale with actual usage (replicas × uptime). Use `min_replicas = 0` in Terraform for dev environments to scale to zero when idle.

---

## Teardown (When Not Needed)

```bash
cd terraform
terraform destroy -auto-approve
```

This removes **all** Azure resources created by this stack.

---

## Phase 9 — Automate Deployment with GitHub Actions

To enable automatic deployment whenever you push to the `main` branch, follow these steps:

### 9.1 Create an Azure Service Principal

GitHub Actions needs a Service Principal to update your Container Apps.

```bash
# Get your Subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create the Service Principal
# This grants 'Contributor' role on the Resource Group
# IMPORTANT: Use --sdk-auth for compatibility with GitHub Actions
az ad sp create-for-rbac \
  --name "omega-nexus-deployer" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-omega-nexus \
  --sdk-auth
```

**IMPORTANT:** Copy the entire JSON output from the command above.

### 9.2 Configure GitHub Secrets

Go to your GitHub Repository → **Settings** → **Secrets and variables** → **Actions** and add these secrets:

| Secret Name | Value |
|---|---|
| `AZURE_CREDENTIALS` | The **FULL JSON** from Phase 9.1 |
| `RG_NAME` | `rg-omega-nexus` |

### 9.3 Troubleshooting "Login failed" Errors

If you see `Login failed ... Ensure 'client-id' and 'tenant-id' are supplied`:

1.  **Check JSON format**: Your `AZURE_CREDENTIALS` secret must be a single block of JSON like this:
    ```json
    {
      "clientId": "...",
      "clientSecret": "...",
      "subscriptionId": "...",
      "tenantId": "..."
    }
    ```
2.  **No extra characters**: Ensure there are no leading/trailing spaces or quotes around the JSON when you paste it into GitHub.
3.  **Correct Repo**: Verify you added the secret to the **Actions** secrets section, not Environments or Dependabot.
