import io
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from main import app

client = TestClient(app)
def headers(user): return {"Authorization": f"Bearer {create_access_token({'sub':user,'email':user+'@test','role':'RESEARCHER'})}"}
def test_mcp_discovery_invocation_and_ownership():
    owner = headers("mcp-owner"); other = headers("mcp-other")
    created = client.post("/api/v1/experiments", headers=owner, json={"title":"MCP experiment"}); assert created.status_code == 201
    exp = created.json()["id"]
    upload = client.post(f"/api/v1/experiments/{exp}/files", headers=owner, files=[("files",("train.py",io.BytesIO(b"import torch\n"),"text/x-python")),("files",("config.yaml",io.BytesIO(b"seed: 3\n"),"text/yaml"))]); assert upload.status_code == 200
    tools = client.get("/api/v1/mcp/tools", headers=owner); assert tools.status_code == 200 and len(tools.json()["tools"]) == 6
    metadata = client.post("/api/v1/mcp/tools/call", headers=owner, json={"name":"get_experiment_metadata","arguments":{"experiment_id":exp}}); assert metadata.status_code == 200 and metadata.json()["result"]["title"] == "MCP experiment"
    files = client.post("/api/v1/mcp/tools/call", headers=owner, json={"name":"get_experiment_files","arguments":{"experiment_id":exp}}); assert files.status_code == 200 and files.json()["result"]["files"]
    assert client.post("/api/v1/mcp/tools/call", headers=other, json={"name":"get_experiment_metadata","arguments":{"experiment_id":exp}}).status_code == 403
    assert client.post("/api/v1/mcp/tools/call", headers=owner, json={"name":"get_file_content","arguments":{"experiment_id":exp,"file_id":"../../secret"}}).status_code == 404
    assert client.post("/api/v1/mcp/tools/call", headers=owner, json={"name":"unknown","arguments":{}}).status_code == 400
