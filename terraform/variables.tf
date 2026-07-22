variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-vigilrag"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "francecentral"
}

variable "vnet_name" {
  description = "Name of the Virtual Network"
  type        = string
  default     = "vnet-vigilrag"
}

variable "snet_aci_name" {
  description = "Name of the subnet delegated to ACI"
  type        = string
  default     = "snet-aci"
}

variable "azure_tenant_id" {
  description = "Azure AD Tenant ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_client_id" {
  description = "Azure AD Application (Client) ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_username" {
  description = "GitHub Username for GHCR"
  type        = string
  default     = ""
}

variable "github_pat" {
  description = "GitHub Personal Access Token (Managed in Azure Portal)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_repo_owner" {
  description = "GitHub Repository Owner (e.g. your-github-username)"
  type        = string
  default     = "your-github-username"
}

variable "gemini_api_key" {
  description = "Gemini API Key for the Agent (Managed in Azure Portal)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "existing_env_name" {
  description = "Name of the existing Container App Environment"
  type        = string
  default     = "nexvocab-env-prod"
}

variable "existing_env_rg" {
  description = "Resource Group of the existing Container App Environment"
  type        = string
  default     = "nexvocab-france"
}
