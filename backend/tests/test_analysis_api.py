import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_experiment_analysis_and_comparison_api():
    # 1. Create Experiment A
    exp_a_res = client.post("/api/v1/experiments", json={
        "title": "Baseline Experiment A",
        "description": "PyTorch CIFAR-10 baseline run",
        "tags": ["baseline", "pytorch"]
    })
    assert exp_a_res.status_code == 201
    exp_a_id = exp_a_res.json()["id"]

    files_a = [
        ("files", ("train.py", io.BytesIO(b"import torch\ntorch.manual_seed(42)\nlr = 0.001"), "text/x-python")),
        ("files", ("requirements.txt", io.BytesIO(b"torch==2.1.0\nnumpy==1.26.0"), "text/plain")),
        ("files", ("config.yaml", io.BytesIO(b"learning_rate: 0.001\nbatch_size: 32\noptimizer: Adam"), "text/yaml")),
        ("files", ("results.csv", io.BytesIO(b"epoch,loss,accuracy\n1,0.8,0.7\n2,0.4,0.85"), "text/csv"))
    ]
    client.post(f"/api/v1/experiments/{exp_a_id}/files", files=files_a)

    # 2. Analyze Experiment A
    analyze_res = client.post(f"/api/v1/experiments/{exp_a_id}/analyze")
    assert analyze_res.status_code == 200
    analysis_data = analyze_res.json()
    assert analysis_data["status"] == "COMPLETED"
    assert analysis_data["overall_score"] > 0
    assert len(analysis_data["reproducibility"]["findings"]) > 0

    # 3. Create Experiment B (Variant)
    exp_b_res = client.post("/api/v1/experiments", json={
        "title": "Variant Experiment B",
        "description": "PyTorch CIFAR-10 high learning rate variant",
        "tags": ["variant", "pytorch"]
    })
    assert exp_b_res.status_code == 201
    exp_b_id = exp_b_res.json()["id"]

    files_b = [
        ("files", ("train.py", io.BytesIO(b"import torch\n# Missing seed\nlr = 0.01"), "text/x-python")),
        ("files", ("requirements.txt", io.BytesIO(b"torch==2.4.0\nnumpy==1.26.0"), "text/plain")),
        ("files", ("config.yaml", io.BytesIO(b"learning_rate: 0.01\nbatch_size: 64\noptimizer: Adam"), "text/yaml")),
        ("files", ("results.csv", io.BytesIO(b"epoch,loss,accuracy\n1,1.2,0.6\n2,0.6,0.78"), "text/csv"))
    ]
    client.post(f"/api/v1/experiments/{exp_b_id}/files", files=files_b)

    # 4. Compare Experiment A vs Experiment B
    compare_res = client.post("/api/v1/compare", json={
        "experiment_a_id": exp_a_id,
        "experiment_b_id": exp_b_id
    })
    assert compare_res.status_code == 200
    compare_data = compare_res.json()

    assert compare_data["experiment_a_id"] == exp_a_id
    assert compare_data["experiment_b_id"] == exp_b_id
    assert len(compare_data["config_diffs"]) >= 1
    assert len(compare_data["dependency_diffs"]) >= 1
    assert len(compare_data["metric_comparisons"]) >= 1

    # Cleanup
    client.delete(f"/api/v1/experiments/{exp_a_id}")
    client.delete(f"/api/v1/experiments/{exp_b_id}")
