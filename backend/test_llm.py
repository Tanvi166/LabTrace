import asyncio

from app.services.llm_service import LLMService


async def main():
    service = LLMService()

    answer = service.generate(
        "What is LabTrace? Answer in two short sentences."
    )

    print("\nGPT-4.1-mini response:\n")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())