import mimetypes
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from azure.core.exceptions import ResourceNotFoundError

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.services.blob_service import BlobStorageService

router = APIRouter()


def _service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, (FileNotFoundError, ResourceNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    # Azure SDK details can disclose account, container, and authentication information.
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Azure Blob Storage request failed")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or ""
    try:
        BlobStorageService.validate_filename(filename)
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValueError("file exceeds the configured maximum upload size")
        service = BlobStorageService()
        service.upload_file(filename, BytesIO(content))
        return {"filename": filename, "container": service.container_name, "status": "uploaded"}
    except Exception as exc:
        raise _service_error(exc)
    finally:
        await file.close()


@router.get("")
def list_files(current_user: User = Depends(get_current_user)):
    try:
        return {"files": BlobStorageService().list_files()}
    except Exception as exc:
        raise _service_error(exc)


@router.get("/{filename}")
def download_file(filename: str, current_user: User = Depends(get_current_user)):
    try:
        content = BlobStorageService().download_file(filename)
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return StreamingResponse(
            BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise _service_error(exc)


@router.delete("/{filename}")
def delete_file(filename: str, current_user: User = Depends(get_current_user)):
    try:
        BlobStorageService().delete_file(filename)
        return {"filename": filename, "status": "deleted"}
    except Exception as exc:
        raise _service_error(exc)
