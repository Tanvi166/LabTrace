#!/bin/bash
set -e

RESOURCE_GROUP="rg-labtrace-prod"
LOCATION="eastus"

echo "Deploying LabTrace to Microsoft Azure..."
az group create --name $RESOURCE_GROUP --location $LOCATION

az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file azure/main.bicep \
  --parameters azure/parameters.json

echo "Azure infrastructure deployment completed."
