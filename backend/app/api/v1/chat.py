from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.rag_service import RAGService

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be empty")
        return value


@router.post("")
async def chat_with_labtrace_context(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Answer a question only from Azure AI Search-retrieved LabTrace context."""
    try:
        result = await RAGService().answer(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        # Preserve service secrets and provider internals at the API boundary.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LabTrace RAG request failed")

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }
