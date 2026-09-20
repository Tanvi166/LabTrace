# RAG

`LocalKnowledgeProvider` chunks administrator-ingested documents deterministically and performs keyword, vector-style, or hybrid retrieval with source and chunk metadata. It is the default test/development mode. `AzureAISearchKnowledgeProvider` is an Azure adapter; it reports configuration failures rather than returning invented citations. Configure an Azure AI Search index and embedding deployment before enabling `KNOWLEDGE_PROVIDER=azure`.
