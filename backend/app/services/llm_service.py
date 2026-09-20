from openai import OpenAI

from app.core.config import settings


class LLMService:
    def __init__(self):
        if not settings.AZURE_FOUNDRY_PROJECT_ENDPOINT:
            raise ValueError(
                "AZURE_FOUNDRY_PROJECT_ENDPOINT is not configured"
            )

        if not settings.AZURE_FOUNDRY_MODEL:
            raise ValueError(
                "AZURE_FOUNDRY_MODEL is not configured"
            )

        if not settings.AZURE_FOUNDRY_API_KEY:
            raise ValueError(
                "AZURE_FOUNDRY_API_KEY is not configured"
            )

        endpoint = settings.AZURE_FOUNDRY_PROJECT_ENDPOINT.rstrip("/")
        base_url = endpoint if endpoint.endswith("/openai/v1") else f"{endpoint}/openai/v1"

        self.client = OpenAI(
            base_url=base_url,
            api_key=settings.AZURE_FOUNDRY_API_KEY,
        )

        self.model = settings.AZURE_FOUNDRY_DEPLOYMENT or settings.AZURE_FOUNDRY_MODEL

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text
