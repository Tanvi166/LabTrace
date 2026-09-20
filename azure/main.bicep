@description('Name prefix for all Azure resources')
param projectName string = 'labtrace'

@description('Azure deployment environment')
param environment string = 'prod'

@description('Azure location for resources')
param location string = resourceGroup().location

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${projectName}${environment}store'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${projectName}-${environment}-env'
  location: location
  properties: {
    zoneRedundant: false
  }
}

output storageAccountName string = storageAccount.name
output containerEnvId string = containerAppEnv.id
