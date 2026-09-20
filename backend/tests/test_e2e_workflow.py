import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token

client = TestClient(app)

def test_full_manual_e2e_workflow():
    # 1 & 2 & 3. Authentication (User token)
    token = create_access_token({"sub": "e2e-user-999", "email": "e2e@labtrace.ai", "role": "RESEARCHER"})
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Create an experiment
    create_res = client.post(
        "/api/v1/experiments",
        headers=headers,
        json={
            "title": "E2E ResNet50 Reproducibility Audit",
            "description": "Full end-to-end experiment verification test",
            "tags": ["resnet", "e2e", "pytorch"]
        }
    )
    assert create_res.status_code == 201
    exp_id = create_res.json()["id"]

    # 5. Upload files: train.py, config.yaml, requirements.txt, results.csv, README.md
    files_payload = [
        ("files", ("train.py", io.BytesIO(b"import torch\nimport torch.nn as nn\nprint('ResNet Training...')"), "text/x-python")),
        ("files", ("config.yaml", io.BytesIO(b"batch_size: 64\nlearning_rate: 0.001\nseed: 42"), "text/yaml")),
        ("files", ("requirements.txt", io.BytesIO(b"torch==2.1.0\ntorchvision==0.16.0\nnumpy==1.26.0"), "text/plain")),
        ("files", ("results.csv", io.BytesIO(b"epoch,train_loss,val_acc\n1,0.85,0.72\n2,0.42,0.88"), "text/csv")),
        ("files", ("README.md", io.BytesIO(b"# ResNet Benchmark\nRun `python train.py` to reproduce."), "text/markdown"))
    ]
    upload_res = client.post(f"/api/v1/experiments/{exp_id}/files", headers=headers, files=files_payload)
    assert upload_res.status_code == 200
    uploaded = upload_res.json()
    assert len(uploaded) == 5

    # 6. Verify files appear in experiment
    get_exp_res = client.get(f"/api/v1/experiments/{exp_id}", headers=headers)
    assert get_exp_res.status_code == 200
    exp_detail = get_exp_res.json()
    assert exp_detail["files_count"] == 5

    # 7 & 8. Open train.py & view file content
    train_file = next(f for f in exp_detail["files"] if f["filename"] == "train.py")
    content_res = client.get(f"/api/v1/experiments/{exp_id}/files/{train_file['id']}", headers=headers)
    assert content_res.status_code == 200
    assert "import torch" in content_res.json()["content"]

    # 9. Delete one file (e.g. README.md)
    readme_file = next(f for f in exp_detail["files"] if f["filename"] == "README.md")
    del_file_res = client.delete(f"/api/v1/experiments/{exp_id}/files/{readme_file['id']}", headers=headers)
    assert del_file_res.status_code == 204

    # 10, 11 & 12. Upload a ZIP archive & verify safe extraction
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w') as zf:
        zf.writestr("model_arch.py", "class ResNetBlock:\n pass")
        zf.writestr("dataset_meta.json", '{"name": "CIFAR-10", "num_classes": 10}')
    zip_buf.seek(0)

    zip_upload_res = client.post(
        f"/api/v1/experiments/{exp_id}/files",
        headers=headers,
        files=[("files", ("model_archive.zip", zip_buf, "application/zip"))]
    )
    assert zip_upload_res.status_code == 200
    extracted = zip_upload_res.json()
    assert len(extracted) == 2

    # 13 & 14. Try malicious ZIP path traversal & verify rejection
    mal_zip_buf = io.BytesIO()
    with zipfile.ZipFile(mal_zip_buf, 'w') as zf:
        zf.writestr("../../../etc/shadow", "root:*:0:0:root:/root:/bin/bash")
    mal_zip_buf.seek(0)

    mal_upload_res = client.post(
        f"/api/v1/experiments/{exp_id}/files",
        headers=headers,
        files=[("files", ("malicious.zip", mal_zip_buf, "application/zip"))]
    )
    assert mal_upload_res.status_code == 400
    assert "Path traversal detected" in mal_upload_res.json()["detail"]

    # 15 & 16. Delete experiment & verify storage cleanup
    del_exp_res = client.delete(f"/api/v1/experiments/{exp_id}", headers=headers)
    assert del_exp_res.status_code == 204

    # Verify 404
    assert client.get(f"/api/v1/experiments/{exp_id}", headers=headers).status_code == 404
