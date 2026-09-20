from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LabTrace"

def test_auth_me():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
