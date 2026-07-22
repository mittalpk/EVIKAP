#!/bin/bash
# ── VigilRAG State Fix Script ──
# Run this to sync your Azure resources with Terraform
# Usage: SUB_ID=<your-subscription-id> ./fix_state.sh

SUB_ID="${SUB_ID:?Set SUB_ID to your Azure subscription ID before running this script}"
RG="rg-vigilrag"

echo "Syncing Backend..."
terraform import azurerm_container_app.backend /subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.App/containerApps/ca-vigilrag-backend

echo "Syncing Agent..."
terraform import azurerm_container_app.agent /subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.App/containerApps/ca-vigilrag-agent

echo "Syncing Frontend..."
terraform import azurerm_container_app.frontend /subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.App/containerApps/ca-vigilrag-frontend

echo "State sync complete! You can now run 'terraform apply' safely."
