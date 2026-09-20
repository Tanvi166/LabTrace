from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token

client = TestClient(app)

def test_experiment_ownership_isolation():
    # User A token
    token_user_a = create_access_token({"sub": "user-a-111", "email": "usera@labtrace.ai", "role": "RESEARCHER"})
    headers_a = {"Authorization": f"Bearer {token_user_a}"}

    # User B token
    token_user_b = create_access_token({"sub": "user-b-222", "email": "userb@labtrace.ai", "role": "RESEARCHER"})
    headers_b = {"Authorization": f"Bearer {token_user_b}"}

    # User A creates experiment
    resp_a = client.post(
        "/api/v1/experiments",
        headers=headers_a,
        json={"title": "User A Private Experiment"}
    )
    assert resp_a.status_code == 201
    exp_a_id = resp_a.json()["id"]

    # User B attempts to view User A's experiment -> 403 Forbidden
    resp_b_view = client.get(f"/api/v1/experiments/{exp_a_id}", headers=headers_b)
    assert resp_b_view.status_code == 403

    # User B attempts to delete User A's experiment -> 403 Forbidden
    resp_b_delete = client.delete(f"/api/v1/experiments/{exp_a_id}", headers=headers_b)
    assert resp_b_delete.status_code == 403

    # User A deletes their own experiment -> 204
    resp_a_delete = client.delete(f"/api/v1/experiments/{exp_a_id}", headers=headers_a)
    assert resp_a_delete.status_code == 204
