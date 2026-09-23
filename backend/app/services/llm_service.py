from openai import OpenAI

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.is_mock = False
        if not settings.AZURE_FOUNDRY_PROJECT_ENDPOINT or not settings.AZURE_FOUNDRY_MODEL or not settings.AZURE_FOUNDRY_API_KEY:
            self.is_mock = True
            return

        endpoint = settings.AZURE_FOUNDRY_PROJECT_ENDPOINT.rstrip("/")
        base_url = endpoint if endpoint.endswith("/openai/v1") else f"{endpoint}/openai/v1"

        self.client = OpenAI(
            base_url=base_url,
            api_key=settings.AZURE_FOUNDRY_API_KEY,
        )

        self.model = settings.AZURE_FOUNDRY_DEPLOYMENT or settings.AZURE_FOUNDRY_MODEL

    def generate(self, prompt: str) -> str:
        if self.is_mock:
            return "This is a mock LLM response because the Azure AI Foundry Endpoint is not configured in your .env file."

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text
