from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient

from app.core.config import settings


class AzureSearchService:
    def __init__(self):
        self.is_mock = False
        if not settings.AZURE_AI_SEARCH_ENDPOINT or not settings.AZURE_AI_SEARCH_KEY or not settings.AZURE_AI_SEARCH_INDEX_NAME:
            self.is_mock = True
            return

        self.client = SearchClient(
            endpoint=settings.AZURE_AI_SEARCH_ENDPOINT,
            index_name=settings.AZURE_AI_SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(settings.AZURE_AI_SEARCH_KEY),
        )

    async def search(
        self,
        query: str,
        top: int = 5,
    ) -> list[dict[str, Any]]:
        if self.is_mock:
            return [
                {
                    "score": 0.95,
                    "chunk_id": "chunk-mock-1",
                    "parent_id": "parent-mock-1",
                    "title": "Mock Documentation",
                    "chunk": f"This is a mock chunk retrieved for query: {query}",
                }
            ]
            
        results = []

        async with self.client:
            response = await self.client.search(
                search_text=query,
                top=top,
                select=[
                    "chunk_id",
                    "parent_id",
                    "chunk",
                    "title",
                ],
            )

            async for result in response:
                results.append(
                    {
                        "score": result.get("@search.score"),
                        "chunk_id": result.get("chunk_id"),
                        "parent_id": result.get("parent_id"),
                        "title": result.get("title"),
                        "chunk": result.get("chunk"),
                    }
                )

        return results