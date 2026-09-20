# LabTrace

## Azure AI / AI-103 Concepts Demonstrated

Implemented locally: deterministic analysis, multi-agent orchestration, grounded document chunking/retrieval, hybrid retrieval scoring, source metadata, local/mock embeddings, secure upload handling, and Azure provider boundaries.

Azure adapters are deliberately not claimed as connected without credentials and resources. Planned configuration-backed integrations are Azure AI Search, Foundry-hosted models and embeddings, Blob Storage, SQL, Entra ID/RBAC, Container Apps, and Application Insights. See `docs/` for setup and deployment boundaries.

## Azure Blob Storage

LabTrace uses the existing private Azure Storage account `labtracefiles3118` and
the existing `research-data` container for the `/api/v1/files` API. Configure
`AZURE_STORAGE_CONNECTION_STRING` and set `STORAGE_PROVIDER=azure` for Azure-backed
experiment storage. Alternatively, leave the connection string unset and sign in
with `az login`; the backend then uses `DefaultAzureCredential` against the account
URL. The dedicated files API always uses the configured Blob container and never
creates containers or public URLs. The existing research PDF is read-only through
the API. Managed Identity/RBAC hardening remains a later security step.

## Azure SQL

Structured application records are stored through SQLAlchemy: experiments,
experiment runs, analysis runs, reports, users, and agent logs. SQLite remains
the local default. To enable the existing Azure SQL database, set
`AZURE_SQL_ENABLED=true` and authenticate locally with `az login`. The backend
uses `DefaultAzureCredential`, ODBC Driver 18, and an Entra access token; it does
not use SQL usernames or passwords. Application startup does not create Azure
SQL tables automatically, and no migration is run automatically. Blob and PDF
contents remain in Azure Blob Storage, not SQL.
