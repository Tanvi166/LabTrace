from typing import Type, TypeVar
import json

from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from app.core.config import settings
from app.agents.providers.base_provider import ModelProvider
from app.agents.providers.mock_provider import MockLocalModelProvider

T = TypeVar("T", bound=BaseModel)


class AzureFoundryAgentProvider(ModelProvider):
    """
    Calls Azure AI Foundry Agents.

    Each agent can specify its own Azure Foundry
    agent name and version.
    """

    def __init__(
        self,
        agent_name: str | None = None,
        agent_version: str | None = None,
    ):
        self.endpoint = settings.AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT

        self.agent_name = (
            agent_name
            or settings.AZURE_FOUNDRY_AGENT_NAME
        )

        self.agent_version = (
            agent_version
            or settings.AZURE_FOUNDRY_AGENT_VERSION
            or "2"
        )

        self.fallback = MockLocalModelProvider()

        if not self.endpoint:
            raise ValueError(
                "AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT is not configured"
            )

        if not self.agent_name:
            raise ValueError(
                "Azure Foundry agent name is not configured"
            )

        self.project_client = AIProjectClient(
            endpoint=self.endpoint,
            credential=DefaultAzureCredential(),
        )

        self.openai_client = (
            self.project_client.get_openai_client()
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> str:

        full_prompt = prompt

        if system_prompt:
            full_prompt = (
                f"System instructions:\n{system_prompt}\n\n"
                f"User request:\n{prompt}"
            )

        response = self.openai_client.responses.create(
            input=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            extra_body={
                "agent_reference": {
                    "name": self.agent_name,
                    "version": self.agent_version,
                    "type": "agent_reference",
                }
            },
        )

        return response.output_text

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: str = "",
    ) -> T:

        full_prompt = ""

        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"

        full_prompt += (
            f"{prompt}\n\n"
            "Return ONLY valid JSON matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )

        response = self.openai_client.responses.create(
            input=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            extra_body={
                "agent_reference": {
                    "name": self.agent_name,
                    "version": self.agent_version,
                    "type": "agent_reference",
                }
            },
        )

        raw_output = response.output_text.strip()

        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Azure Foundry agent did not return valid JSON.\n"
                f"Response:\n{raw_output}"
            ) from exc

        return schema.model_validate(parsed)


def get_model_provider(
    agent_name: str | None = None,
    agent_version: str | None = None,
) -> ModelProvider:

    if settings.AZURE_FOUNDRY_AGENT_PROJECT_ENDPOINT:
        return AzureFoundryAgentProvider(
            agent_name=agent_name,
            agent_version=agent_version,
        )

    return MockLocalModelProvider()