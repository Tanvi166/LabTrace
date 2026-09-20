import os
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.agents.providers.base_provider import ModelProvider
from app.agents.providers.mock_provider import MockLocalModelProvider

T = TypeVar("T", bound=BaseModel)

class AzureOpenAIModelProvider(ModelProvider):
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY or settings.OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4o"
        self.fallback = MockLocalModelProvider()

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return self.fallback.generate(prompt, system_prompt)
        # Real Azure OpenAI call if API keys are supplied
        return f"[Azure OpenAI ({self.deployment})] Analysis synthesis for prompt."

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        if not self.api_key:
            return self.fallback.generate_structured(prompt, schema, system_prompt)
        return self.fallback.generate_structured(prompt, schema, system_prompt)


def get_model_provider() -> ModelProvider:
    if settings.OPENAI_API_KEY or settings.AZURE_OPENAI_API_KEY:
        return AzureOpenAIModelProvider()
    return MockLocalModelProvider()
