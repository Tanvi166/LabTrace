"""Safe access to the pre-existing private LabTrace Blob container."""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any, BinaryIO

from app.services.storage_service import AzureBlobStorageProvider


_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,254}$")
_PROTECTED_BLOBS = frozenset({"LabTrace_Research_Experiment_Report.pdf"})


class BlobStorageService:
    """Perform file operations in the configured container without provisioning Azure resources."""

    def __init__(self, provider: AzureBlobStorageProvider | None = None):
        self.provider = provider or AzureBlobStorageProvider()
        self.container_name = self.provider.container_name

    @staticmethod
    def validate_filename(filename: str) -> str:
        if not isinstance(filename, str) or not _SAFE_FILENAME.fullmatch(filename):
            raise ValueError("filename must be a single safe file name")
        return filename

    def upload_file(self, filename: str, file_obj: BinaryIO) -> None:
        filename = self.validate_filename(filename)
        self._ensure_mutable(filename)
        self.provider.container.get_blob_client(filename).upload_blob(file_obj, overwrite=True)

    def list_files(self) -> list[dict[str, Any]]:
        return [
            {"name": blob.name}
            for blob in self.provider.container.list_blobs()
            if self._is_safe_existing_name(blob.name)
        ]

    def download_file(self, filename: str) -> bytes:
        filename = self.validate_filename(filename)
        return self.provider.container.get_blob_client(filename).download_blob().readall()

    def delete_file(self, filename: str) -> None:
        filename = self.validate_filename(filename)
        self._ensure_mutable(filename)
        self.provider.container.get_blob_client(filename).delete_blob()

    @staticmethod
    def _is_safe_existing_name(name: str) -> bool:
        """Expose only root blobs addressable through the public file routes."""
        return bool(_SAFE_FILENAME.fullmatch(name))

    @staticmethod
    def _ensure_mutable(filename: str) -> None:
        if filename in _PROTECTED_BLOBS:
            raise ValueError("the configured research source cannot be modified or deleted")


def bytes_as_file(data: bytes) -> BytesIO:
    """Small helper for callers that already hold an uploaded file in memory."""
    return BytesIO(data)
