import pytest
from azure.core.exceptions import ServiceRequestError
from fastapi.testclient import TestClient

from main import app
import app.api.v1.rag as rag_route
from app.services.knowledge_service import (
    AzureAISearchKnowledgeProvider,
    AzureKnowledgeIndexingError,
    EmbeddingProvider,
)


class FakeIndexingResult:
    def __init__(self, key, succeeded=True):
        self.key = key
        self.succeeded = succeeded


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.inputs = []

    def embed(self, text: str) -> list[float]:
        self.inputs.append(text)
        return [0.1, 0.2, 0.3]


class FakeSearchClient:
    def __init__(self, indexing_results=None):
        self.indexing_results = indexing_results
        self.merge_or_uploaded_documents = []
        self.search_kwargs = None

    def merge_or_upload_documents(self, *, documents):
        self.merge_or_uploaded_documents.append(documents)
        return self.indexing_results or [FakeIndexingResult(document["chunk_id"]) for document in documents]

    def search(self, **kwargs):
        self.search_kwargs = kwargs
        return [
            {
                "@search.score": 1.25,
                "chunk_id": "doc-1-0",
                "parent_id": "doc-1",
                "chunk": "Pinned dependencies improve reproducibility.",
                "title": "Reproducibility guide",
            }
        ]

    def get_document_count(self):
        return 7


@pytest.fixture
def azure_settings(monkeypatch):
    monkeypatch.setattr("app.services.knowledge_service.settings.AZURE_AI_SEARCH_ENDPOINT", "https://example.search.windows.net")
    monkeypatch.setattr("app.services.knowledge_service.settings.AZURE_AI_SEARCH_KEY", "test-key")
    monkeypatch.setattr("app.services.knowledge_service.settings.AZURE_AI_SEARCH_INDEX_NAME", "rag-index")
    monkeypatch.setattr("app.services.knowledge_service.settings.AZURE_AI_SEARCH_VECTOR_FIELD", "text_vector")


def test_keyword_search_is_lexical_only(azure_settings):
    client = FakeSearchClient()
    provider = AzureAISearchKnowledgeProvider(client=client)

    results = provider.search(" reproducibility ", top_k=3, mode="keyword")

    assert client.search_kwargs == {
        "search_text": "reproducibility",
        "top": 3,
        "select": ["chunk_id", "parent_id", "chunk", "title"],
    }
    assert results[0].chunk_id == "doc-1-0"
    assert results[0].document_id == "doc-1"
    assert results[0].source == "doc-1"
    assert results[0].score == 1.25


@pytest.mark.parametrize("mode,expected_search_text", [("vector", None), ("hybrid", "reproducibility")])
def test_vector_and_hybrid_search_construct_vectorized_queries(azure_settings, mode, expected_search_text):
    client = FakeSearchClient()
    embeddings = FakeEmbeddingProvider()
    provider = AzureAISearchKnowledgeProvider(client=client, embedding_provider=embeddings)

    provider.search("reproducibility", top_k=4, mode=mode)

    assert embeddings.inputs == ["reproducibility"]
    assert client.search_kwargs["search_text"] == expected_search_text
    assert client.search_kwargs["top"] == 4
    vector_query = client.search_kwargs["vector_queries"][0]
    assert vector_query.as_dict() == {
        "vector": [0.1, 0.2, 0.3],
        "fields": "text_vector",
        "k": 4,
        "kind": "vector",
    }


def test_azure_provider_rejects_invalid_search_requests(azure_settings):
    provider = AzureAISearchKnowledgeProvider(client=FakeSearchClient())

    with pytest.raises(ValueError, match="query"):
        provider.search(" ")
    with pytest.raises(ValueError, match="top_k"):
        provider.search("query", top_k=21)
    with pytest.raises(ValueError, match="mode"):
        provider.search("query", mode="semantic")


def test_deterministic_document_identity_and_upsert_payload(azure_settings):
    client = FakeSearchClient()
    provider = AzureAISearchKnowledgeProvider(client=client)

    first = provider.ingest("Guide", "docs/guide.md", "Pin dependency versions.")
    second = provider.ingest("Guide", "docs/guide.md", "Pin dependency versions.")

    assert first[0].document_id == second[0].document_id
    assert first[0].chunk_id == second[0].chunk_id
    assert len(client.merge_or_uploaded_documents) == 2
    payload = client.merge_or_uploaded_documents[0][0]

    assert payload["chunk_id"] == first[0].chunk_id
    assert payload["parent_id"] == first[0].document_id
    assert payload["chunk"] == "Pin dependency versions."
    assert payload["title"] == "Guide"

    assert "text_vector" in payload
    assert len(payload["text_vector"]) == 3072


def test_explicit_document_id_keeps_chunk_ids_and_can_include_vectors(azure_settings):
    client = FakeSearchClient()
    embeddings = FakeEmbeddingProvider()
    provider = AzureAISearchKnowledgeProvider(client=client, embedding_provider=embeddings)

    first = provider.ingest("Guide", "docs/guide.md", "Set random seeds.", document_id="guide-v1")
    second = provider.ingest("Guide", "docs/guide.md", "Set random seeds.", document_id="guide-v1")

    assert first[0].chunk_id == second[0].chunk_id == "guide-v1-0"
    assert client.merge_or_uploaded_documents[0][0] == {
        "chunk_id": "guide-v1-0",
        "parent_id": "guide-v1",
        "chunk": "Set random seeds.",
        "title": "Guide",
        "text_vector": [0.1, 0.2, 0.3],
    }
    assert embeddings.inputs == ["Set random seeds.", "Set random seeds."]


def test_partial_indexing_failure_surfaces_safe_chunk_identifiers(azure_settings, caplog):
    client = FakeSearchClient(indexing_results=[FakeIndexingResult("doc-1-0", succeeded=False)])
    provider = AzureAISearchKnowledgeProvider(client=client)

    with pytest.raises(AzureKnowledgeIndexingError, match="doc-1-0") as exc:
        provider.ingest("Guide", "source", "content", document_id="doc-1")

    assert exc.value.document_id == "doc-1"
    assert exc.value.failed_chunk_ids == ["doc-1-0"]
    assert "document_id=doc-1" in caplog.text


def test_azure_provider_requires_configuration(monkeypatch):
    monkeypatch.setattr("app.services.knowledge_service.settings.AZURE_AI_SEARCH_ENDPOINT", None)

    with pytest.raises(RuntimeError, match="AZURE_AI_SEARCH_ENDPOINT"):
        AzureAISearchKnowledgeProvider(client=FakeSearchClient())


def test_rag_route_returns_safe_azure_sdk_error(monkeypatch):
    class FailingProvider:
        def search(self, *args, **kwargs):
            raise ServiceRequestError("network details must not reach clients")

    monkeypatch.setattr(rag_route, "get_knowledge_provider", lambda: FailingProvider())
    response = TestClient(app).post("/api/v1/rag/search", json={"query": "reproducibility"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Azure AI Search request failed"}
