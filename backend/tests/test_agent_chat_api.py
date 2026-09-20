from fastapi.testclient import TestClient

from main import app
import app.api.v1.agent_chat as agent_chat_route
from app.services.agent_service import FoundryAgentService

client = TestClient(app)


def test_agent_chat_endpoint_returns_answer_and_foundry_sources(monkeypatch):
    class FakeFoundryAgentService:
        def answer(self, question: str):
            assert question == "What random seed was used?"
            return {
                "answer": "The random seed used in the experiments was 42.",
                "sources": [
                    {"type": "azure_ai_search_call", "id": "call_123", "status": "completed"},
                    {"type": "url_citation", "title": "Experiment notes", "url": "https://example.test/notes"},
                ],
            }

    monkeypatch.setattr(agent_chat_route, "FoundryAgentService", FakeFoundryAgentService)
    response = client.post("/api/v1/agent/chat", json={"question": "  What random seed was used?  "})

    assert response.status_code == 200
    assert response.json() == {
        "question": "What random seed was used?",
        "answer": "The random seed used in the experiments was 42.",
        "sources": [
            {"type": "azure_ai_search_call", "id": "call_123", "status": "completed"},
            {"type": "url_citation", "title": "Experiment notes", "url": "https://example.test/notes"},
        ],
    }


def test_agent_chat_endpoint_hides_provider_errors(monkeypatch):
    class FailingFoundryAgentService:
        def answer(self, question: str):
            raise RuntimeError("credential=secret-value")

    monkeypatch.setattr(agent_chat_route, "FoundryAgentService", FailingFoundryAgentService)
    response = client.post("/api/v1/agent/chat", json={"question": "Question"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Foundry Agent request failed"}


def test_foundry_agent_service_uses_pinned_version_and_preserves_sources(monkeypatch):
    monkeypatch.setattr("app.services.agent_service.settings.AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT", "https://example.test/project")
    monkeypatch.setattr("app.services.agent_service.settings.AZURE_FOUNDRY_AGENT_NAME", "test")
    monkeypatch.setattr("app.services.agent_service.settings.AZURE_FOUNDRY_AGENT_VERSION", "3")

    class FakeResponses:
        def create(self, *, input: str):
            assert input == "What random seed was used?"
            return {
                "output_text": "The random seed used in the experiments was 42.",
                "output": [
                    {"type": "azure_ai_search_call", "id": "search_call", "status": "completed"},
                    {"type": "message", "content": [{"annotations": [{
                        "type": "url_citation", "url_citation": {"title": "Results", "url": "https://example.test/results"}
                    }]}]},
                ],
            }

    class FakeProjectClient:
        class agents:
            @staticmethod
            def get_version(agent_name: str, agent_version: str):
                assert (agent_name, agent_version) == ("test", "3")

            @staticmethod
            def get(agent_name: str):
                assert agent_name == "test"
                return {"versions": {"latest": {"version": "3"}}}

        @staticmethod
        def get_openai_client(*, agent_name: str):
            assert agent_name == "test"
            return type("FakeOpenAIClient", (), {"responses": FakeResponses()})()

    result = FoundryAgentService(project_client=FakeProjectClient()).answer(" What random seed was used? ")

    assert result == {
        "answer": "The random seed used in the experiments was 42.",
        "sources": [
            {"type": "azure_ai_search_call", "id": "search_call", "status": "completed"},
            {"type": "url_citation", "url_citation": {"title": "Results", "url": "https://example.test/results"}},
        ],
    }
