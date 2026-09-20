import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_file_upload_and_content_retrieval():
    # 1. Create experiment
    exp_resp = client.post("/api/v1/experiments", json={"title": "File Upload Test Run"})
    exp_id = exp_resp.json()["id"]

    # 2. Upload Python script & CSV metrics
    files = [
        ("files", ("train.py", io.BytesIO(b"import torch\nprint('Training started...')"), "text/x-python")),
        ("files", ("metrics.csv", io.BytesIO(b"epoch,loss,accuracy\n1,0.5,0.8\n2,0.3,0.9"), "text/csv"))
    ]
    upload_resp = client.post(f"/api/v1/experiments/{exp_id}/files", files=files)
    assert upload_resp.status_code == 200
    uploaded_files = upload_resp.json()
    assert len(uploaded_files) == 2

    py_file_id = next(f["id"] for f in uploaded_files if f["original_filename"] == "train.py")

    # 3. Read file content
    content_resp = client.get(f"/api/v1/experiments/{exp_id}/files/{py_file_id}")
    assert content_resp.status_code == 200
    content_data = content_resp.json()
    assert "import torch" in content_data["content"]
    assert content_data["is_binary"] is False

    # 4. Delete single file
    del_file_resp = client.delete(f"/api/v1/experiments/{exp_id}/files/{py_file_id}")
    assert del_file_resp.status_code == 204

    # 5. Clean up experiment
    client.delete(f"/api/v1/experiments/{exp_id}")

def test_unsupported_file_extension_rejection():
    exp_resp = client.post("/api/v1/experiments", json={"title": "Malicious Extension Test"})
    exp_id = exp_resp.json()["id"]

    files = [("files", ("evil_payload.exe", io.BytesIO(b"binary data"), "application/x-msdownload"))]
    upload_resp = client.post(f"/api/v1/experiments/{exp_id}/files", files=files)
    assert upload_resp.status_code == 415

    client.delete(f"/api/v1/experiments/{exp_id}")
