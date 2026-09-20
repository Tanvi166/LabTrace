"""Read-only access to the configured, smoke-tested Foundry Agent."""

from typing import Any, Iterable

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from app.core.config import settings


def _value(value: Any, name: str, default: Any = None) -> Any:
    """Read SDK model fields whether a test double supplies a dict or object."""
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def _required(value: str | None, setting_name: str) -> str:
    if not value:
        raise ValueError(f"{setting_name} must be configured for Foundry Agent chat")
    return value


class FoundryAgentService:
    """Invoke only the configured existing Foundry Agent version.

    This service intentionally performs no agent, connection, index, model, or
    other Azure resource creation.  The agent endpoint serves its latest version,
    so the latest-version check prevents a request from being routed to a version
    other than the pinned, smoke-tested one.
    """

    def __init__(self, project_client: AIProjectClient | None = None):
        self.endpoint = _required(
            settings.AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT,
            "AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT",
        )
        self.agent_name = _required(settings.AZURE_FOUNDRY_AGENT_NAME, "AZURE_FOUNDRY_AGENT_NAME")
        self.agent_version = _required(
            settings.AZURE_FOUNDRY_AGENT_VERSION, "AZURE_FOUNDRY_AGENT_VERSION"
        )
        self.project_client = project_client or AIProjectClient(
            endpoint=self.endpoint,
            credential=DefaultAzureCredential(),
            allow_preview=True,
        )

    def answer(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")

        # Read calls only: ensure version 3 still exists and is the version that
        # the agent endpoint will invoke.  Do not fall forward to a new version.
        self.project_client.agents.get_version(self.agent_name, self.agent_version)
        agent = self.project_client.agents.get(self.agent_name)
        latest = _value(_value(agent, "versions", {}), "latest")
        latest_version = _value(latest, "version")
        if str(latest_version) != str(self.agent_version):
            raise ValueError(
                "Configured Foundry Agent version is not the active version; request was not sent"
            )

        response = self.project_client.get_openai_client(agent_name=self.agent_name).responses.create(
            input=question.strip()
        )
        return {
            "answer": _value(response, "output_text", ""),
            "sources": self._sources(_value(response, "output", []) or []),
        }

    @staticmethod
    def _sources(items: Iterable[Any]) -> list[dict[str, Any]]:
        """Keep safe Azure AI Search/tool metadata and message citations."""
        sources: list[dict[str, Any]] = []
        for item in items:
            item_type = _value(item, "type")
            if item_type and item_type != "message":
                metadata = {
                    key: value
                    for key, value in {
                        "type": item_type,
                        "id": _value(item, "id"),
                        "status": _value(item, "status"),
                    }.items()
                    if value is not None
                }
                if metadata:
                    sources.append(metadata)

            for content in _value(item, "content", []) or []:
                for annotation in _value(content, "annotations", []) or []:
                    citation = {
                        key: value
                        for key, value in {
                            "type": _value(annotation, "type"),
                            "title": _value(annotation, "title"),
                            "url": _value(annotation, "url"),
                            "text": _value(annotation, "text"),
                        }.items()
                        if value is not None
                    }
                    for nested_name in ("url_citation", "file_citation"):
                        nested = _value(annotation, nested_name)
                        if nested:
                            citation[nested_name] = {
                                key: _value(nested, key)
                                for key in ("title", "url", "file_id", "text")
                                if _value(nested, key) is not None
                            }
                    if citation:
                        sources.append(citation)
        return sources
