"""Grounded local retrieval and an Azure AI Search adapter (no fabricated Azure results)."""
from __future__ import annotations
import hashlib, json, math, re, uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from app.core.config import settings

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
        if not (settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT): raise RuntimeError("Azure embedding endpoint, key, and deployment are required")
        try: from openai import AzureOpenAI
        except ImportError as exc: raise RuntimeError("Install openai to enable Azure embeddings") from exc
        self.client = AzureOpenAI(api_key=settings.AZURE_OPENAI_API_KEY, azure_endpoint=settings.AZURE_OPENAI_ENDPOINT, api_version="2024-02-01")
    def embed(self, text: str) -> list[float]: return list(self.client.embeddings.create(model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT, input=text).data[0].embedding)

def chunk_document(content: str, document_id: str, title: str, source: str, chunk_size: int = 900, overlap: int = 120) -> list[KnowledgeChunk]:
    if chunk_size <= overlap: raise ValueError("chunk_size must exceed overlap")
    words = re.findall(r"\S+", content); output = []; start = ordinal = 0
    while start < len(words):
        end = start; length = 0
        while end < len(words) and length + len(words[end]) + 1 <= chunk_size: length += len(words[end]) + 1; end += 1
        end = max(end, start + 1); output.append(KnowledgeChunk(document_id, f"{document_id}:{ordinal}", title, source, " ".join(words[start:end]))); ordinal += 1
        if end >= len(words): break
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
class AzureAISearchKnowledgeProvider(KnowledgeProvider):
    def __init__(self):
        if not (settings.AZURE_AI_SEARCH_ENDPOINT and settings.AZURE_AI_SEARCH_KEY): raise RuntimeError("Azure AI Search endpoint and key are required")
        try:
            from azure.core.credentials import AzureKeyCredential; from azure.search.documents import SearchClient
        except ImportError as exc: raise RuntimeError("Install azure-search-documents to enable Azure AI Search") from exc
        self.client=SearchClient(settings.AZURE_AI_SEARCH_ENDPOINT,settings.AZURE_AI_SEARCH_INDEX_NAME,AzureKeyCredential(settings.AZURE_AI_SEARCH_KEY))
    def ingest(self,*args,**kwargs): raise RuntimeError("Azure AI Search ingestion requires an Azure embedding deployment; configure it before use")
    def search(self,*args,**kwargs): raise RuntimeError("Azure AI Search retrieval requires an Azure embedding deployment; configure it before use")
    def health(self):
        try: self.client.get_document_count(); return {"provider":"azure_ai_search","connected":True}
        except Exception as exc: return {"provider":"azure_ai_search","connected":False,"detail":type(exc).__name__}
def get_knowledge_provider() -> KnowledgeProvider: return AzureAISearchKnowledgeProvider() if settings.KNOWLEDGE_PROVIDER.lower()=="azure" else LocalKnowledgeProvider()
