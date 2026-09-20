import io
import re

from fastapi.testclient import TestClient

from main import app
import app.api.v1.files as files_route
from app.services.blob_service import BlobStorageService

client = TestClient(app)


def _mock_service(monkeypatch, *, files=None, content=b"report", error=None):
    class FakeBlobStorageService:
        container_name = "research-data"

        @staticmethod
        def validate_filename(filename):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,254}", filename or ""):
                raise ValueError("filename must be a single safe file name")
            return filename

        def upload_file(self, filename, file_obj):
            self.validate_filename(filename)
            if error:
                raise error
            assert file_obj.read() == b"new experiment"

        def list_files(self):
            if error:
                raise error
            return files if files is not None else [{"name": "LabTrace_Research_Experiment_Report.pdf"}]

        def download_file(self, filename):
            self.validate_filename(filename)
            if error:
                raise error
            return content

        def delete_file(self, filename):
            self.validate_filename(filename)
            if error:
                raise error

    monkeypatch.setattr(files_route, "BlobStorageService", FakeBlobStorageService)


def test_blob_upload_endpoint(monkeypatch):
    _mock_service(monkeypatch)

    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("experiment.txt", io.BytesIO(b"new experiment"), "text/plain")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "filename": "experiment.txt",
        "container": "research-data",
        "status": "uploaded",
    }


def test_blob_list_endpoint(monkeypatch):
    _mock_service(monkeypatch, files=[{"name": "LabTrace_Research_Experiment_Report.pdf"}])

    response = client.get("/api/v1/files")

    assert response.status_code == 200
    assert response.json() == {"files": [{"name": "LabTrace_Research_Experiment_Report.pdf"}]}


def test_blob_download_endpoint(monkeypatch):
    _mock_service(monkeypatch, content=b"downloaded report")

    response = client.get("/api/v1/files/experiment.txt")

    assert response.status_code == 200
    assert response.content == b"downloaded report"
    assert response.headers["content-disposition"] == 'attachment; filename="experiment.txt"'


def test_blob_delete_endpoint(monkeypatch):
    _mock_service(monkeypatch)

    response = client.delete("/api/v1/files/experiment.txt")

    assert response.status_code == 200
    assert response.json() == {"filename": "experiment.txt", "status": "deleted"}


def test_blob_routes_reject_unsafe_filenames(monkeypatch):
    _mock_service(monkeypatch)

    upload = client.post(
        "/api/v1/files/upload",
        files={"file": ("../secret.txt", io.BytesIO(b"new experiment"), "text/plain")},
    )
    download = client.get("/api/v1/files/%2E%2E%5Csecret.txt")

    assert upload.status_code == 400
    assert download.status_code == 400


def test_blob_service_protects_existing_research_source():
    class FakeContainer:
        def get_blob_client(self, filename):
            raise AssertionError(f"protected blob must not be accessed: {filename}")

    provider = type("FakeProvider", (), {"container_name": "research-data", "container": FakeContainer()})()
    service = BlobStorageService(provider=provider)

    for operation in (
        lambda: service.upload_file("LabTrace_Research_Experiment_Report.pdf", io.BytesIO(b"replacement")),
        lambda: service.delete_file("LabTrace_Research_Experiment_Report.pdf"),
    ):
        try:
            operation()
        except ValueError as exc:
            assert "cannot be modified or deleted" in str(exc)
        else:
            raise AssertionError("protected research PDF mutation was allowed")


def test_blob_routes_hide_azure_errors(monkeypatch):
    _mock_service(monkeypatch, error=RuntimeError("connection-string=secret"))

    response = client.get("/api/v1/files")

    assert response.status_code == 502
    assert response.json() == {"detail": "Azure Blob Storage request failed"}
