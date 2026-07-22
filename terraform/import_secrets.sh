#!/bin/bash
# Import existing Key Vault secrets into Terraform state
# Usage: SUBSCRIPTION_ID=<your-sub-id> KV_NAME=<your-key-vault-name> ./import_secrets.sh

set -e

# Azure details
SUBSCRIPTION_ID="${SUBSCRIPTION_ID:?Set SUBSCRIPTION_ID to your Azure subscription ID before running this script}"
RG_NAME="rg-vigilrag"
KV_NAME="${KV_NAME:?Set KV_NAME to your Key Vault name before running this script}"
KV_URI="https://${KV_NAME}.vault.azure.net/"

echo "Importing existing Key Vault secrets into Terraform state..."
echo "Key Vault: $KV_NAME"
echo "Resource Group: $RG_NAME"
echo "Subscription: $SUBSCRIPTION_ID"
echo ""

# Function to import a secret using vault URI format
import_secret() {
    local secret_name=$1
    local resource_id=$2
    
    # Vault URI format (correct for Terraform)
    local import_id="${KV_URI}secrets/${secret_name}"
    
    echo "Importing secret: $secret_name"
    echo "  Import ID: $import_id"
    terraform import \
        "azurerm_key_vault_secret.$resource_id" \
        "$import_id" \
        && echo "✅ Imported: $secret_name" \
        || echo "⚠️  Error importing: $secret_name"
    echo ""
}

# Import all existing secrets
import_secret "github-pat" "github_pat"
import_secret "gemini-api-key" "gemini_api_key"
import_secret "azure-storage-connection-string" "azure_storage_connection_string"
import_secret "admin-username" "admin_username"
import_secret "admin-password" "admin_password"
import_secret "X-Internal-API-Key" "internal_api_key"

echo ""
echo "✅ Import complete!"
echo ""
echo "Next step: Run 'terraform plan' to verify all resources are properly managed"
echo ""
echo "If any imports failed, run manually:"
echo "  terraform import azurerm_key_vault_secret.<name> '${KV_URI}secrets/<secret-name>'"
