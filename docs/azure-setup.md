# Azure setup

Manual configuration is pending. Required resources: Azure AI Search, Blob Storage, a Foundry/OpenAI chat deployment, an embedding deployment, Azure SQL or another SQLAlchemy-compatible database, Container Apps, Application Insights, and an Entra application registration. Use managed identity where available and grant only Blob Data Contributor, Search Index Data Reader/Contributor as required, and model inference access. Never expose keys to the frontend.
