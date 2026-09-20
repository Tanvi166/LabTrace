from typing import Type, TypeVar
from pydantic import BaseModel
from app.agents.providers.base_provider import ModelProvider

T = TypeVar("T", bound=BaseModel)

class MockLocalModelProvider(ModelProvider):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Local Heuristic Agent Output] Analyzed context using deterministic rules.\nPrompt summary: {prompt[:100]}..."

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        # Construct dummy/fallback instance of schema for zero-dependency local runs
        # Real agents override and fill schema directly from Phase 3 analysis outputs
        try:
            return schema.model_construct()
        except Exception:
            return schema()
