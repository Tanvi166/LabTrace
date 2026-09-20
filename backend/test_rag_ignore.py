__test__ = False
import asyncio

from app.services.rag_service import RAGService


async def main():
    question = "What random seed was used in the experiments?"
    result = await RAGService().answer(question)

    print("Question:")
    print(question)
    print("\nGenerated answer:")
    print(result["answer"])
    print("\nSources:")
    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    asyncio.run(main())
