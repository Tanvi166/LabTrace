# LabTrace architecture

Deterministic Python analysis is the source of truth. The FastAPI orchestration layer passes only extracted evidence to agents, which interpret and report it. Local knowledge retrieval persists chunks under `backend/data/knowledge`; Azure mode uses Azure AI Search when configured.

Cloud responsibilities: Foundry hosts model calls; AI Search retrieves guidance; Blob stores uploads; SQL stores ORM data; Entra authenticates users; Container Apps hosts the service; Application Insights receives safe operational telemetry.
