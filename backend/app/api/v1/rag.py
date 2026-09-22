from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from azure.core.exceptions import AzureError
import logging
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.knowledge_service import get_knowledge_provider

router = APIRouter()
logger = logging.getLogger(__name__)
class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    mode: str = Field(default="hybrid", pattern="^(keyword|vector|hybrid)$")
class IngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=1000)
    content: str = Field(min_length=1, max_length=2_000_000)
    document_id: str | None = Field(default=None, min_length=1, max_length=200)


def _azure_error(exc: AzureError) -> HTTPException:
    logger.warning("Azure AI Search request failed: %s", type(exc).__name__)
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Azure AI Search request failed")

@router.post("/search")
def search_guidance(request: SearchRequest, current_user: User = Depends(get_current_user)):
    try: return {"results": [item.__dict__ for item in get_knowledge_provider().search(request.query, request.top_k, request.mode)]}
    except AzureError as exc: raise _azure_error(exc)
    except (ValueError, RuntimeError) as exc: raise HTTPException(status_code=400, detail=str(exc))
@router.post("/documents", status_code=status.HTTP_201_CREATED)
def ingest_document(request: IngestRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN": raise HTTPException(status_code=403, detail="Only administrators can ingest knowledge documents")
    try:
        chunks = get_knowledge_provider().ingest(request.title, request.source, request.content, request.document_id)
        return {"document_id": chunks[0].document_id, "chunks_created": len(chunks)}
    except AzureError as exc: raise _azure_error(exc)
    except (ValueError, RuntimeError) as exc: raise HTTPException(status_code=400, detail=str(exc))
@router.get("/status")
def rag_status(current_user: User = Depends(get_current_user)):
    try: return get_knowledge_provider().health()
    except RuntimeError as exc: return {"provider":"azure_ai_search", "connected":False, "detail":str(exc)}
