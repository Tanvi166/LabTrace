from typing import Type, TypeVar
from pydantic import BaseModel
from app.agents.providers.base_provider import ModelProvider

T = TypeVar("T", bound=BaseModel)

class MockLocalModelProvider(ModelProvider):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Local Heuristic Agent Output] Analyzed context using deterministic rules.\nPrompt summary: {prompt[:100]}..."

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        # Construct dummy instance of schema for zero-dependency local runs
        dummy_data = {}
        for field_name, field_info in schema.model_fields.items():
            # Quick heuristics for dummy data based on type
            annotation_str = str(field_info.annotation).lower()
            if "list" in annotation_str:
                dummy_data[field_name] = []
            elif "dict" in annotation_str:
                dummy_data[field_name] = {}
            elif "float" in annotation_str:
                dummy_data[field_name] = 85.0
            elif "int" in annotation_str:
                dummy_data[field_name] = 1
            elif "str" in annotation_str:
                dummy_data[field_name] = f"Mock {field_name.replace('_', ' ')}"
            else:
                dummy_data[field_name] = None
        try:
            return schema(**dummy_data)
        except Exception:
            return schema.model_construct(**dummy_data)
