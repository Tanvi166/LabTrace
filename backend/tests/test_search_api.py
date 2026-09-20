from fastapi.testclient import TestClient

from main import app
import app.api.v1.search as search_route


client = TestClient(app)


def test_azure_search_endpoint_returns_service_results(monkeypatch):
    class FakeAzureSearchService:
        async def search(self, query: str):
            assert query == "LabTrace"
            return [{"title": "LabTrace", "chunk_id": "chunk-1", "chunk": "Indexed text", "score": 0.9}]

    monkeypatch.setattr(search_route, "AzureSearchService", FakeAzureSearchService)
    response = client.get("/api/v1/search", params={"q": "LabTrace"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "LabTrace",
        "count": 1,
        "results": [{"title": "LabTrace", "chunk_id": "chunk-1", "chunk": "Indexed text", "score": 0.9}],
    }
