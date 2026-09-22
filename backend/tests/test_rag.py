from app.services.knowledge_service import LocalKnowledgeProvider, chunk_document

def test_chunking_and_local_hybrid_retrieval(tmp_path):
    chunks = chunk_document("Random seeds make training reproducible. Pin dependency versions.", "doc-1", "Guide", "Test")
    assert chunks and chunks[0].chunk_id == "doc-1-0"
    provider = LocalKnowledgeProvider(str(tmp_path))
    provider.ingest("Guide", "Test source", "Set random seeds and pin dependency versions for reproducible experiments.")
    result = provider.search("random seed reproducibility", mode="hybrid")
    assert result[0].source == "Test source"
    assert result[0].chunk_id
