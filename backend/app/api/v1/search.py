from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.search_service import AzureSearchService

router = APIRouter()


@router.get("")
async def search_azure_ai_search(
    q: str = Query(..., min_length=1, max_length=2000, description="Search query"),
    current_user: User = Depends(get_current_user),
):
    """Search the configured Azure AI Search index and return indexed chunks."""
    try:
        results = await AzureSearchService().search(q)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception:
        # Do not leak Azure credentials, connection details, or service internals.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Azure AI Search request failed")

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
