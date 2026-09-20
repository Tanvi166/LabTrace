from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_experiment_crud_flow():
    # Create experiment
    create_resp = client.post(
        "/api/v1/experiments",
        json={
            "title": "PyTorch ResNet Training Run",
            "description": "ImageNet benchmark with ResNet50",
            "tags": ["vision", "resnet", "pytorch"]
        }
    )
    assert create_resp.status_code == 201
    exp_data = create_resp.json()
    exp_id = exp_data["id"]
    assert exp_data["title"] == "PyTorch ResNet Training Run"
    assert exp_data["status"] == "CREATED"
    assert len(exp_data["tags"]) == 3

    # Retrieve single experiment
    get_resp = client.get(f"/api/v1/experiments/{exp_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == exp_id

    # List experiments
    list_resp = client.get("/api/v1/experiments?page=1&page_size=10")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == exp_id for item in list_data["items"])

    # Update experiment
    patch_resp = client.patch(
        f"/api/v1/experiments/{exp_id}",
        json={"title": "Updated ResNet Run Title"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Updated ResNet Run Title"

    # Delete experiment
    del_resp = client.delete(f"/api/v1/experiments/{exp_id}")
    assert del_resp.status_code == 204

    # Verify 404 after deletion
    get_404 = client.get(f"/api/v1/experiments/{exp_id}")
    assert get_404.status_code == 404
