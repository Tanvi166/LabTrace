import io
import zipfile
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_safe_zip_extraction():
    exp_resp = client.post("/api/v1/experiments", json={"title": "Safe Zip Test"})
    exp_id = exp_resp.json()["id"]

    # Create valid ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("model.py", "import torch\nclass Net:\n pass")
        zf.writestr("config.yaml", "lr: 0.001\nbatch_size: 32")
    zip_buffer.seek(0)

    files = [("files", ("experiment_code.zip", zip_buffer, "application/zip"))]
    upload_resp = client.post(f"/api/v1/experiments/{exp_id}/files", files=files)
    assert upload_resp.status_code == 200
    extracted_files = upload_resp.json()
    assert len(extracted_files) == 2
    filenames = [f["original_filename"] for f in extracted_files]
    assert "model.py" in filenames
    assert "config.yaml" in filenames

    client.delete(f"/api/v1/experiments/{exp_id}")

def test_zip_path_traversal_rejection():
    exp_resp = client.post("/api/v1/experiments", json={"title": "Malicious Zip Test"})
    exp_id = exp_resp.json()["id"]

    # Create malicious ZIP with path traversal entry "../../evil.py"
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("../../evil_system_override.py", "import os; os.system('echo hacked')")
    zip_buffer.seek(0)

    files = [("files", ("malicious_traversal.zip", zip_buffer, "application/zip"))]
    upload_resp = client.post(f"/api/v1/experiments/{exp_id}/files", files=files)
    assert upload_resp.status_code == 400
    assert "Path traversal detected" in upload_resp.json()["detail"]

    client.delete(f"/api/v1/experiments/{exp_id}")
