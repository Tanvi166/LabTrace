import asyncio

from app.services.search_service import AzureSearchService


async def main():
    service = AzureSearchService()

    results = await service.search(
        "What is LabTrace and what problem does it solve?",
        top=5,
    )

    print(f"\nFound {len(results)} results\n")

    for i, result in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print("Score:", result["score"])
        print("Title:", result["title"])
        print("Chunk ID:", result["chunk_id"])
        print("Text:")
        print(result["chunk"][:1000])
        print()


if __name__ == "__main__":
    asyncio.run(main())