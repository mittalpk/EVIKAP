provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "nexus" {
  name     = var.resource_group_name
  location = var.location
}

# User-Assigned Managed Identity for Container Apps to access Key Vault
resource "azurerm_user_assigned_identity" "nexus_identity" {
  name                = "id-vigilrag"
  location            = azurerm_resource_group.nexus.location
  resource_group_name = azurerm_resource_group.nexus.name
}

# Virtual Network for Sandboxes
resource "azurerm_virtual_network" "nexus_vnet" {
  name                = var.vnet_name
  location            = azurerm_resource_group.nexus.location
  resource_group_name = azurerm_resource_group.nexus.name
  address_space       = ["10.0.0.0/16"]

  depends_on = [azurerm_resource_group.nexus]
}

# Subnet dedicated and delegated to Azure Container Instances
resource "azurerm_subnet" "aci_subnet" {
  name                 = var.snet_aci_name
  resource_group_name  = azurerm_resource_group.nexus.name
  virtual_network_name = azurerm_virtual_network.nexus_vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  depends_on = [azurerm_virtual_network.nexus_vnet]

  delegation {
    name = "aciDelegation"

    service_delegation {
      name    = "Microsoft.ContainerInstance/containerGroups"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action", "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"]
    }
  }
}

# Network Security Group to restrict egress traffic
resource "azurerm_network_security_group" "aci_nsg" {
  name                = "nsg-aci-sandboxes"
  location            = azurerm_resource_group.nexus.location
  resource_group_name = azurerm_resource_group.nexus.name

  security_rule {
    name                       = "AllowInternalVNet"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  security_rule {
    name                       = "DenyInternetEgress"
    priority                   = 200
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "Internet"
  }
}

resource "azurerm_subnet_network_security_group_association" "aci_subnet_nsg" {
  subnet_id                 = azurerm_subnet.aci_subnet.id
  network_security_group_id = azurerm_network_security_group.aci_nsg.id
}

# ── Fetch Existing Container Apps Environment ──────────────────────────────────
data "azurerm_container_app_environment" "nexus_env" {
  name                = var.existing_env_name
  resource_group_name = var.existing_env_rg
}

# ── Key Vault for Secrets ─────────────────────────────────────────────────────
resource "azurerm_key_vault" "nexus_kv" {
  name                        = "kv-vigilrag-${substr(data.azurerm_client_config.current.subscription_id, 0, 8)}"
  location                    = azurerm_resource_group.nexus.location
  resource_group_name         = azurerm_resource_group.nexus.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = true

  sku_name = "standard"

  # Deployer (CI service principal / developer) — full management permissions
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Set", "Get", "List", "Delete", "Purge", "Recover"
    ]
  }

  # Managed identity used by Container Apps — read-only
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.nexus_identity.principal_id

    secret_permissions = [
      "Get", "List"
    ]
  }

  depends_on = [azurerm_user_assigned_identity.nexus_identity]
}

# ── Key Vault Secrets ──────────────────────────────────────────────────────
# Production secrets - use ignore_changes to avoid overwriting manually-set values
# Before applying, set secrets in Azure:
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name internal-api-key --value "<secure-value>"
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name github-pat --value "<token>"
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name azure-storage-connection-string --value "<connection>"
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name admin-username --value "<username>"
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name admin-password --value "<password>"
#   az keyvault secret set --vault-name kv-vigilrag-XXXXX --name gemini-api-key --value "<key>"

resource "azurerm_key_vault_secret" "internal_api_key" {
  name         = "internal-api-key"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

resource "azurerm_key_vault_secret" "github_pat" {
  name         = "github-pat"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

resource "azurerm_key_vault_secret" "azure_storage_connection_string" {
  name         = "azure-storage-connection-string"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

resource "azurerm_key_vault_secret" "admin_username" {
  name         = "admin-username"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

resource "azurerm_key_vault_secret" "admin_password" {
  name         = "admin-password"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

resource "azurerm_key_vault_secret" "gemini_api_key" {
  name         = "gemini-api-key"
  value        = "CHANGE_ME_IN_PRODUCTION"
  key_vault_id = azurerm_key_vault.nexus_kv.id

  lifecycle {
    ignore_changes = [value]
  }

  depends_on = [azurerm_key_vault.nexus_kv]
}

# ── Container App: Backend ──────────────────────────────────────────────────
resource "azurerm_container_app" "backend" {
  name                         = "ca-vigilrag-backend"
  container_app_environment_id = data.azurerm_container_app_environment.nexus_env.id
  resource_group_name          = azurerm_resource_group.nexus.name
  revision_mode                = "Single"
  depends_on = [
    azurerm_key_vault.nexus_kv,
    azurerm_key_vault_secret.internal_api_key,
    azurerm_key_vault_secret.github_pat,
    azurerm_key_vault_secret.azure_storage_connection_string,
    azurerm_key_vault_secret.admin_username,
    azurerm_key_vault_secret.admin_password
  ]
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.nexus_identity.id]
  }

  template {
    container {
      name   = "backend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 1.0
      memory = "2.0Gi"

      env {
        name        = "GITHUB_PAT"
        secret_name = "github-pat"
      }

      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "azure-storage-connection-string"
      }

      env {
        name        = "ADMIN_USERNAME"
        secret_name = "admin-username"
      }

      env {
        name        = "ADMIN_PASSWORD"
        secret_name = "admin-password"
      }

      env {
        name        = "INTERNAL_API_KEY"
        secret_name = "internal-api-key"
      }

      env {
        name  = "AGENT_SERVICE_URL"
        value = "http://ca-vigilrag-agent:8000"
      }

      env {
        name  = "AGENT_FQDN"
        value = "https://ca-vigilrag-agent.${data.azurerm_container_app_environment.nexus_env.default_domain}"
      }

      readiness_probe {
        port                    = 8000
        transport               = "HTTP"
        path                    = "/health"
        interval_seconds        = 10
        failure_count_threshold = 3
      }
      liveness_probe {
        port      = 8000
        transport = "HTTP"
        path      = "/health"
      }
      startup_probe {
        port      = 8000
        transport = "HTTP"
        path      = "/health"
      }
    }
    min_replicas = 1
    max_replicas = 5
  }

  secret {
    name                = "github-pat"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/github-pat/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  secret {
    name                = "azure-storage-connection-string"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/azure-storage-connection-string/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  secret {
    name                = "admin-username"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/admin-username/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  secret {
    name                = "admin-password"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/admin-password/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  secret {
    name                = "internal-api-key"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/internal-api-key/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].container[0].image
    ]
  }
}

# ── Container App: Agent ────────────────────────────────────────────────────
resource "azurerm_container_app" "agent" {
  name                         = "ca-vigilrag-agent"
  container_app_environment_id = data.azurerm_container_app_environment.nexus_env.id
  resource_group_name          = azurerm_resource_group.nexus.name
  revision_mode                = "Single"
  depends_on = [
    azurerm_key_vault.nexus_kv,
    azurerm_key_vault_secret.internal_api_key,
    azurerm_key_vault_secret.gemini_api_key
  ]
  template {
    container {
      name   = "agent"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 1.0
      memory = "2.0Gi"

      env {
        name        = "GEMINI_API_KEY"
        secret_name = "gemini-api-key"
      }

      env {
        name        = "INTERNAL_API_KEY"
        secret_name = "internal-api-key"
      }

      env {
        name  = "BACKEND_URL"
        value = "https://ca-vigilrag-backend.${data.azurerm_container_app_environment.nexus_env.default_domain}"
      }

      readiness_probe {
        port                    = 8000
        transport               = "HTTP"
        path                    = "/health"
        interval_seconds        = 10
        failure_count_threshold = 3
      }
      liveness_probe {
        port      = 8000
        transport = "HTTP"
        path      = "/health"
      }
      startup_probe {
        port      = 8000
        transport = "HTTP"
        path      = "/health"
      }
    }
    min_replicas = 1
    max_replicas = 10
  }

  secret {
    name                = "gemini-api-key"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/gemini-api-key/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  secret {
    name                = "internal-api-key"
    key_vault_secret_id = "${azurerm_key_vault.nexus_kv.vault_uri}secrets/internal-api-key/"
    identity            = azurerm_user_assigned_identity.nexus_identity.id
  }

  ingress {
    external_enabled = false
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.nexus_identity.id]
  }

  lifecycle {
    ignore_changes = [
      template[0].container[0].image
    ]
  }
}

# ── Container App: Frontend ─────────────────────────────────────────────────
resource "azurerm_container_app" "frontend" {
  name                         = "ca-vigilrag-frontend"
  container_app_environment_id = data.azurerm_container_app_environment.nexus_env.id
  resource_group_name          = azurerm_resource_group.nexus.name
  revision_mode                = "Single"

  depends_on = [
    azurerm_container_app.backend,
    azurerm_container_app.agent
  ]

  template {
    container {
      name   = "frontend"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
    min_replicas = 1
    max_replicas = 5
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "backend_url" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}
