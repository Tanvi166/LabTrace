from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generates plain text response."""
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        """Generates structured Pydantic response."""
        pass
