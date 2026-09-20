import io

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from main import app


client = TestClient(app)


def _headers(user_id: str = "phase4-user") -> dict[str, str]:
    token = create_access_token({"sub": user_id, "email": f"{user_id}@labtrace.ai", "role": "RESEARCHER"})
    return {"Authorization": f"Bearer {token}"}


def _create_experiment(title: str, learning_rate: str, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/experiments", headers=headers, json={"title": title, "tags": ["phase4"]})
    assert response.status_code == 201
    experiment_id = response.json()["id"]
    files = [
        ("files", ("train.py", io.BytesIO(b"import torch\ntorch.manual_seed(42)\n"), "text/x-python")),
        ("files", ("config.yaml", io.BytesIO(f"learning_rate: {learning_rate}\nbatch_size: 32\n".encode()), "text/yaml")),
        ("files", ("requirements.txt", io.BytesIO(b"torch==2.1.0\nnumpy==1.26.0\n"), "text/plain")),
        ("files", ("results.csv", io.BytesIO(b"epoch,accuracy\n1,0.70\n2,0.85\n"), "text/csv")),
    ]
    assert client.post(f"/api/v1/experiments/{experiment_id}/files", headers=headers, files=files).status_code == 200
    return experiment_id


def test_authenticated_ai_workflow_persists_agents_report_and_comparison():
    headers = _headers()
    exp_a = _create_experiment("Phase 4 baseline", "0.001", headers)
    exp_b = _create_experiment("Phase 4 variant", "0.01", headers)

    analysis = client.post(f"/api/v1/experiments/{exp_a}/ai-analyze", headers=headers)
    assert analysis.status_code == 200, analysis.text
    payload = analysis.json()
    assert payload["status"] == "COMPLETED"
    assert payload["analysis_run_id"]
    assert payload["report_id"]

    run = client.get(f"/api/v1/analysis-runs/{payload['analysis_run_id']}", headers=headers)
    assert run.status_code == 200
    assert run.json()["status"] == "COMPLETED"
    assert set(run.json()["completed_agents"]) == {
        "Coordinator Agent", "Metadata Agent", "Code Analysis Agent", "Results Agent", "Reproducibility Agent", "Knowledge Agent", "Report Agent"
    }

    logs = client.get(f"/api/v1/analysis-runs/{payload['analysis_run_id']}/agents", headers=headers)
    assert logs.status_code == 200
    assert len(logs.json()) == 7
    assert any(log["agent_name"] == "Knowledge Agent" for log in logs.json())
    assert all(log["status"] == "COMPLETED" for log in logs.json())

    calls = client.get("/api/v1/mcp/calls", headers=headers)
    assert calls.status_code == 200
    assert {call["name"] for call in calls.json()["calls"]} >= {
        "get_experiment_metadata", "get_experiment_files", "get_file_content",
        "get_experiment_results", "get_reproducibility_findings",
    }
    assert all(call["status"] == "COMPLETED" for call in calls.json()["calls"])

    deterministic = client.post(f"/api/v1/experiments/{exp_a}/analyze", headers=headers)
    assert deterministic.status_code == 200
    workflow_runs = client.get("/api/v1/agents/runs", headers=headers)
    assert workflow_runs.status_code == 200
    assert all(run["agent_count"] > 0 for run in workflow_runs.json())

    report = client.get(f"/api/v1/reports/{payload['report_id']}", headers=headers)
    assert report.status_code == 200
    assert report.json()["structured_json"]["overall_score"] == payload["overall_score"]
    assert report.json()["structured_json"]["findings"]
    assert client.get("/api/v1/reports", headers=headers).status_code == 200
    assert client.get("/api/v1/agents/runs", headers=headers).status_code == 200

    comparison = client.post("/api/v1/compare/ai", headers=headers, json={"experiment_a_id": exp_a, "experiment_b_id": exp_b})
    assert comparison.status_code == 200, comparison.text
    assert comparison.json()["status"] == "COMPLETED"

    foreign = client.get(f"/api/v1/analysis-runs/{payload['analysis_run_id']}", headers=_headers("other-user"))
    assert foreign.status_code == 403


def test_mcp_failure_is_logged_without_aborting_the_workflow(monkeypatch):
    import app.services.tool_provider as tool_provider

    headers = _headers("mcp-failure-user")
    experiment_id = _create_experiment("MCP failure experiment", "0.001", headers)
    original_invoke = tool_provider.invoke_tool

    def failing_results_tool(name, arguments, db, user):
        if name == "get_experiment_results":
            raise RuntimeError("results tool unavailable")
        return original_invoke(name, arguments, db, user)

    monkeypatch.setattr(tool_provider, "invoke_tool", failing_results_tool)
    response = client.post(f"/api/v1/experiments/{experiment_id}/ai-analyze", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "FAILED"

    run = client.get(f"/api/v1/analysis-runs/{payload['analysis_run_id']}", headers=headers)
    assert "Results Agent" in run.json()["failed_agents"]
    assert "Report Agent" in run.json()["completed_agents"]

    calls = client.get("/api/v1/mcp/calls", headers=headers).json()["calls"]
    failed_call = next(call for call in calls if call["name"] == "get_experiment_results")
    assert failed_call["status"] == "FAILED"
    assert failed_call["error"] == "results tool unavailable"
