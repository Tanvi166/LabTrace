"""Grounded local retrieval and an Azure AI Search adapter (no fabricated Azure results)."""
from __future__ import annotations
import hashlib, json, logging, math, re, uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeChunk:
    document_id: str; chunk_id: str; title: str; source: str; content: str; section: str | None = None
@dataclass
class KnowledgeSearchResult:
    title: str; content: str; source: str; score: float; chunk_id: str; document_id: str; section: str | None = None

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...
class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int | None = None):
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS
        if self.dimensions < 2: raise ValueError("EMBEDDING_DIMENSIONS must be at least 2")
    def embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9_]+", text.lower()): values[int(hashlib.sha256(token.encode()).hexdigest(), 16) % self.dimensions] += 1
        norm = math.sqrt(sum(value * value for value in values)); return [value / norm for value in values] if norm else values
class AzureEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        endpoint = settings.AZURE_OPENAI_ENDPOINT or settings.AZURE_FOUNDRY_PROJECT_ENDPOINT
        api_key = settings.AZURE_OPENAI_API_KEY or settings.AZURE_FOUNDRY_API_KEY
        if endpoint and endpoint.rstrip("/").endswith("/openai/v1"):
            endpoint = endpoint.rstrip("/").removesuffix("/openai/v1")
        if not (endpoint and api_key and settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT): raise RuntimeError("Azure embedding endpoint, key, and deployment are required")
        try: from openai import AzureOpenAI
        except ImportError as exc: raise RuntimeError("Install openai to enable Azure embeddings") from exc
        self.client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version="2024-02-01")
        self.deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    def embed(self, text: str) -> list[float]: return list(self.client.embeddings.create(model=self.deployment, input=text).data[0].embedding)

def chunk_document(
    content: str,
    document_id: str,
    title: str,
    source: str,
    chunk_size: int = 900,
    overlap: int = 120,
) -> list[KnowledgeChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must exceed overlap")

    words = re.findall(r"\S+", content)
    output = []
    start = ordinal = 0

    # Azure AI Search document keys cannot contain "/".
    safe_document_id = re.sub(r"[^A-Za-z0-9_=~-]", "_", document_id)
    while start < len(words):
        end = start
        length = 0

        while (
            end < len(words)
            and length + len(words[end]) + 1 <= chunk_size
        ):
            length += len(words[end]) + 1
            end += 1

        end = max(end, start + 1)

        chunk_id = f"{safe_document_id}-{ordinal}"

        output.append(
            KnowledgeChunk(
                document_id=document_id,
                chunk_id=chunk_id,
                title=title,
                source=source,
                content=" ".join(words[start:end]),
            )
        )

        ordinal += 1

        if end >= len(words):
            break

        start = max(start + 1, end - max(1, overlap // 8))

    return output

class KnowledgeProvider(ABC):
    @abstractmethod
    def ingest(self, title: str, source: str, content: str, document_id: str | None = None) -> list[KnowledgeChunk]: ...
    @abstractmethod
    def search(self, query: str, top_k: int = 5, mode: str = "hybrid") -> list[KnowledgeSearchResult]: ...
    @abstractmethod
    def health(self) -> dict[str, Any]: ...
class LocalKnowledgeProvider(KnowledgeProvider):
    def __init__(self, path: str | None = None): self.path = Path(path or settings.LOCAL_KNOWLEDGE_PATH); self.path.mkdir(parents=True, exist_ok=True); self.store = self.path / "chunks.json"; self.embeddings = MockEmbeddingProvider()
    def _all(self): return [] if not self.store.exists() else [KnowledgeChunk(**item) for item in json.loads(self.store.read_text(encoding="utf-8"))]
    def ingest(self, title, source, content, document_id=None):
        if not content.strip(): raise ValueError("Document content must not be empty")
        chunks = chunk_document(content, document_id or str(uuid.uuid4()), title, source); self.store.write_text(json.dumps([asdict(c) for c in [*self._all(), *chunks]]), encoding="utf-8"); return chunks
    def search(self, query, top_k=5, mode="hybrid"):
        if not query.strip() or not 1 <= top_k <= 20 or mode not in {"keyword","vector","hybrid"}: raise ValueError("Invalid query, top_k, or retrieval mode")
        terms = set(re.findall(r"[a-z0-9_]+", query.lower())); q = self.embeddings.embed(query); ranked=[]
        for chunk in self._all():
            keyword=len(terms & set(re.findall(r"[a-z0-9_]+", chunk.content.lower())))/max(len(terms),1); vector=sum(a*b for a,b in zip(q,self.embeddings.embed(chunk.content))); score=keyword if mode=="keyword" else vector if mode=="vector" else (keyword+vector)/2
            if score: ranked.append((score,chunk))
        return [KnowledgeSearchResult(c.title,c.content,c.source,round(s,6),c.chunk_id,c.document_id,c.section) for s,c in sorted(ranked,reverse=True,key=lambda x:x[0])[:top_k]]
    def health(self): return {"provider":"local","connected":True,"chunks":len(self._all())}
class AzureKnowledgeIndexingError(RuntimeError):
    """A safe, retryable summary of an Azure Search partial indexing failure."""

    def __init__(self, document_id: str, failed_chunk_ids: list[str]):
        self.document_id = document_id
        self.failed_chunk_ids = failed_chunk_ids
        super().__init__(
            f"Azure AI Search rejected chunks for document {document_id}: {', '.join(failed_chunk_ids)}"
        )


class AzureAISearchKnowledgeProvider(KnowledgeProvider):
    """Azure AI Search provider for the verified lexical and vector index schema.

    ``parent_id`` persists the document identifier. The existing index has no
    ``source`` field, so Azure result mapping uses ``parent_id`` as its source
    fallback. No index schema is created or modified by this provider.
    """

    _SELECT_FIELDS = ["chunk_id", "parent_id", "chunk", "title"]

    def __init__(self, client: Any | None = None, embedding_provider: EmbeddingProvider | None = None):
        if not settings.AZURE_AI_SEARCH_ENDPOINT:
            raise RuntimeError("AZURE_AI_SEARCH_ENDPOINT is required for Azure knowledge")
        if not settings.AZURE_AI_SEARCH_KEY:
            raise RuntimeError("AZURE_AI_SEARCH_KEY is required for Azure knowledge")
        if not settings.AZURE_AI_SEARCH_INDEX_NAME:
            raise RuntimeError("AZURE_AI_SEARCH_INDEX_NAME is required for Azure knowledge")

        if client is None:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient
            except ImportError as exc:
                raise RuntimeError("Install azure-search-documents to enable Azure AI Search") from exc
            client = SearchClient(
                settings.AZURE_AI_SEARCH_ENDPOINT,
                settings.AZURE_AI_SEARCH_INDEX_NAME,
                AzureKeyCredential(settings.AZURE_AI_SEARCH_KEY),
            )
        self.client = client
        self.embedding_provider = embedding_provider

    @staticmethod
    def _validate_query(query: str, top_k: int, mode: str) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")
        if mode not in {"keyword", "vector", "hybrid"}:
            raise ValueError("mode must be keyword, vector, or hybrid")

    @staticmethod
    def _document_id(source: str, content: str, document_id: str | None) -> str:
        if document_id:
            return document_id
        digest = hashlib.sha256(f"{source}\0{content}".encode("utf-8")).hexdigest()
        return f"doc-{digest}"

    @staticmethod
    def _embedding_is_configured() -> bool:
        return bool(
            (settings.AZURE_OPENAI_ENDPOINT or settings.AZURE_FOUNDRY_PROJECT_ENDPOINT)
            and (settings.AZURE_OPENAI_API_KEY or settings.AZURE_FOUNDRY_API_KEY)
            and settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )

    def _embedding_provider(self) -> EmbeddingProvider:
        if self.embedding_provider is None:
            self.embedding_provider = AzureEmbeddingProvider()
        return self.embedding_provider

    def _vector_query(self, query: str, top_k: int) -> Any:
        try:
            from azure.search.documents.models import VectorizedQuery
        except ImportError as exc:
            raise RuntimeError("Install azure-search-documents to enable vector search") from exc
        vector = self._embedding_provider().embed(query)
        return VectorizedQuery(
            vector=vector,
            fields=settings.AZURE_AI_SEARCH_VECTOR_FIELD,
            k_nearest_neighbors=top_k,
        )

    def ingest(self, title: str, source: str, content: str, document_id: str | None = None) -> list[KnowledgeChunk]:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Document content must not be empty")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Document title must not be empty")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Document source must not be empty")

        document_id = self._document_id(source, content, document_id)
        chunks = chunk_document(content, document_id, title, source)
        include_vectors = self.embedding_provider is not None or self._embedding_is_configured()
        documents = [
            {
                "chunk_id": chunk.chunk_id,
                "parent_id": chunk.document_id,
                "chunk": chunk.content,
                "title": chunk.title,
            }
            for chunk in chunks
        ]
        if include_vectors:
            for document, chunk in zip(documents, chunks, strict=True):
                document[settings.AZURE_AI_SEARCH_VECTOR_FIELD] = self._embedding_provider().embed(chunk.content)

        results = self.client.merge_or_upload_documents(documents=documents)
        def succeeded(result: Any) -> bool:
            return bool(result.get("succeeded", False) if isinstance(result, dict) else getattr(result, "succeeded", False))
        failed = [result for result in results if not succeeded(result)]
        if failed:
            failed_chunk_ids = [
                str(result.get("key") if isinstance(result, dict) else getattr(result, "key", "unknown"))
                for result in failed
            ]
            logger.warning("Azure AI Search partial indexing failure document_id=%s chunks=%s", document_id, failed_chunk_ids)
            raise AzureKnowledgeIndexingError(document_id, failed_chunk_ids)
        return chunks

    def search(self, query: str, top_k: int = 5, mode: str = "hybrid") -> list[KnowledgeSearchResult]:
        self._validate_query(query, top_k, mode)
        search_kwargs: dict[str, Any] = {"top": top_k, "select": self._SELECT_FIELDS}
        if mode == "keyword":
            search_kwargs["search_text"] = query.strip()
        elif mode == "vector":
            search_kwargs["search_text"] = None
            search_kwargs["vector_queries"] = [self._vector_query(query.strip(), top_k)]
        else:
            search_kwargs["search_text"] = query.strip()
            search_kwargs["vector_queries"] = [self._vector_query(query.strip(), top_k)]
        response = self.client.search(**search_kwargs)
        results = []
        for item in response:
            chunk_id = item.get("chunk_id")
            parent_id = item.get("parent_id")
            results.append(
                KnowledgeSearchResult(
                    title=item.get("title") or "Untitled document",
                    content=item.get("chunk") or "",
                    source=parent_id or "Azure AI Search",
                    score=float(item.get("@search.score") or 0.0),
                    chunk_id=chunk_id or "",
                    document_id=parent_id or "",
                )
            )
        return results

    def health(self):
        try:
            return {"provider": "azure_ai_search", "connected": True, "chunks": self.client.get_document_count()}
        except Exception as exc:
            return {"provider": "azure_ai_search", "connected": False, "detail": type(exc).__name__}
def get_knowledge_provider() -> KnowledgeProvider: return AzureAISearchKnowledgeProvider() if settings.KNOWLEDGE_PROVIDER.lower()=="azure" else LocalKnowledgeProvider()
