from fastapi.testclient import TestClient

from main import app
import app.api.v1.chat as chat_route

client = TestClient(app)


def test_chat_endpoint_returns_rag_answer_and_sources(monkeypatch):
    class FakeRAGService:
        async def answer(self, question: str):
            assert question == "What random seed was used?"
            return {
                "answer": "The supplied context states that seed 42 was used.",
                "sources": [{"title": "Experiment notes", "chunk_id": "chunk-42", "score": 1.0}],
            }

    monkeypatch.setattr(chat_route, "RAGService", FakeRAGService)
    response = client.post("/api/v1/chat", json={"question": "  What random seed was used?  "})

    assert response.status_code == 200
    assert response.json() == {
        "question": "What random seed was used?",
        "answer": "The supplied context states that seed 42 was used.",
        "sources": [{"title": "Experiment notes", "chunk_id": "chunk-42", "score": 1.0}],
    }


def test_chat_endpoint_rejects_blank_question():
    response = client.post("/api/v1/chat", json={"question": "   "})
    assert response.status_code == 422
