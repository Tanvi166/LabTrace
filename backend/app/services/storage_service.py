import os
import shutil
import hashlib
import re
from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO
from app.core.config import settings

class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, experiment_id: str, filename: str, file_obj: BinaryIO) -> str:
        """Uploads file content and returns local/remote relative storage path."""
        pass

    @abstractmethod
    def download_file(self, storage_path: str) -> bytes:
        """Reads file bytes from storage."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    def file_exists(self, storage_path: str) -> bool:
        """Checks if file exists in storage."""
        pass

    @abstractmethod
    def list_files(self, experiment_id: str) -> List[str]:
        """Lists file paths for an experiment."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or settings.LOCAL_STORAGE_PATH
        os.makedirs(self.base_path, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        # Strip directory path component to prevent path traversal
        clean_name = os.path.basename(filename)
        # Keep alphanumeric, dot, underscore, dash
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
        return clean_name or "uploaded_file"

    def _get_safe_path(self, relative_path: str) -> str:
        full_path = os.path.abspath(os.path.join(self.base_path, relative_path))
        base_abs = os.path.abspath(self.base_path)
        if not full_path.startswith(base_abs):
            raise ValueError("Path traversal attempt detected.")
        return full_path

    def upload_file(self, experiment_id: str, filename: str, file_obj: BinaryIO) -> str:
        clean_filename = self._sanitize_filename(filename)
        rel_dir = os.path.join(experiment_id)
        target_dir = self._get_safe_path(rel_dir)
        os.makedirs(target_dir, exist_ok=True)

        rel_path = os.path.join(experiment_id, clean_filename)
        full_path = self._get_safe_path(rel_path)

        with open(full_path, "wb") as f:
            shutil.copyfileobj(file_obj, f)

        return rel_path

    def download_file(self, storage_path: str) -> bytes:
        full_path = self._get_safe_path(storage_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {storage_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_path: str) -> bool:
        try:
            full_path = self._get_safe_path(storage_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    def file_exists(self, storage_path: str) -> bool:
        try:
            full_path = self._get_safe_path(storage_path)
            return os.path.exists(full_path)
        except Exception:
            return False

    def list_files(self, experiment_id: str) -> List[str]:
        target_dir = self._get_safe_path(experiment_id)
        if not os.path.exists(target_dir):
            return []
        files = []
        for root, _, filenames in os.walk(target_dir):
            for fname in filenames:
                full_fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(full_fpath, self.base_path)
                files.append(rel_path)
        return files


class AzureBlobStorageProvider(StorageProvider):
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise RuntimeError("Install azure-storage-blob to enable Azure Blob storage") from exc

        # Connection strings remain available for local development. In Azure or
        # an Azure CLI-authenticated workstation, DefaultAzureCredential avoids
        # placing a storage secret in the environment.
        if self.connection_string:
            self.client = BlobServiceClient.from_connection_string(self.connection_string)
        else:
            from azure.identity import DefaultAzureCredential

            account_url = (
                settings.AZURE_STORAGE_ACCOUNT_URL
                or f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            )
            self.client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
        self.container = self.client.get_container_client(self.container_name)

    def upload_file(self, experiment_id: str, filename: str, file_obj: BinaryIO) -> str:
        clean_filename = LocalStorageProvider()._sanitize_filename(filename)
        rel_path = f"{experiment_id}/{clean_filename}"
        self.container.get_blob_client(rel_path).upload_blob(file_obj, overwrite=True)
        return rel_path

    def download_file(self, storage_path: str) -> bytes:
        return self.container.get_blob_client(storage_path).download_blob().readall()

    def delete_file(self, storage_path: str) -> bool:
        try:
            self.container.get_blob_client(storage_path).delete_blob()
            return True
        except Exception:
            return False

    def file_exists(self, storage_path: str) -> bool:
        return self.container.get_blob_client(storage_path).exists()

    def list_files(self, experiment_id: str) -> List[str]:
        return [blob.name for blob in self.container.list_blobs(name_starts_with=f"{experiment_id}/")]


def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_PROVIDER.lower() == "azure":
        return AzureBlobStorageProvider()
    return LocalStorageProvider()
