"""Manually verify the configured Azure Blob container without touching existing blobs.

Run from ``backend`` only after setting ``AZURE_STORAGE_CONNECTION_STRING``:
``python blob_storage_smoke_test.py``.
"""

from io import BytesIO
from uuid import uuid4

from app.services.blob_service import BlobStorageService


def main() -> None:
    service = BlobStorageService()
    filename = f"labtrace-smoke-{uuid4().hex}.txt"
    payload = b"LabTrace Azure Blob Storage smoke test"
    uploaded = False

    try:
        service.upload_file(filename, BytesIO(payload))
        uploaded = True
        assert any(item["name"] == filename for item in service.list_files())
        assert service.download_file(filename) == payload
        service.delete_file(filename)
        uploaded = False
        assert all(item["name"] != filename for item in service.list_files())
        print(f"Azure Blob smoke test passed for {filename} in {service.container_name}.")
    finally:
        # Never touch the existing research PDF; cleanup is limited to this UUID-named blob.
        if uploaded:
            service.delete_file(filename)


if __name__ == "__main__":
    main()
