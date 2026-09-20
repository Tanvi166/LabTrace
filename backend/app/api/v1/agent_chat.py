from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.v1.chat import ChatRequest
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.agent_service import FoundryAgentService

router = APIRouter()


@router.post("/chat")
async def chat_with_foundry_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Answer through the pinned, Azure AI Search-grounded Foundry Agent."""
    try:
        result = await run_in_threadpool(FoundryAgentService().answer, request.question)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        # Never expose provider details, credentials, endpoint URLs, or SDK errors.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Foundry Agent request failed",
        )

    return {"question": request.question, "answer": result["answer"], "sources": result["sources"]}
