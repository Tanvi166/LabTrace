from typing import Any

from app.services.llm_service import LLMService
from app.services.search_service import AzureSearchService


class RAGService:
    """Ground an existing Foundry model call in retrieved Azure AI Search chunks."""

    def __init__(self):
        self.search_service = AzureSearchService()
        self.llm_service = LLMService()

    async def answer(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")

        search_results = await self.search_service.search(question.strip(), top=5)
        sources = [
            {
                "title": result.get("title"),
                "chunk_id": result.get("chunk_id"),
                "score": result.get("score"),
            }
            for result in search_results
        ]

        context = "\n\n".join(
            f"[Source {index}: title={result.get('title')!r}, chunk_id={result.get('chunk_id')!r}]\n"
            f"{result.get('chunk') or ''}"
            for index, result in enumerate(search_results, start=1)
        )
        prompt = f"""Answer the user question using only the supplied LabTrace context.
Do not use outside knowledge, infer missing facts, or invent citations.
If the answer cannot be found in the supplied context, say exactly: "I cannot find the answer in the supplied LabTrace context."

User question:
{question.strip()}

Supplied LabTrace context:
{context or '[No relevant context was retrieved.]'}
"""

        return {
            "answer": self.llm_service.generate(prompt),
            "sources": sources,
        }
