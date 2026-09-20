from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from main import app
from app.api.v1.experiments import ExperimentRunCreate, create_experiment_run
from app.models.experiment import Experiment
from app.models.user import User, UserRole

client = TestClient(app)


def _experiment_id() -> str:
    response = client.post("/api/v1/experiments", json={"title": "Azure SQL metadata test"})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_list_experiment_runs():
    experiment_id = _experiment_id()
    payload = {
        "run_id": "run-baseline-42",
        "status": "COMPLETED",
        "model_name": "gpt-4.1-mini",
        "dataset_version": "v2026.09",
        "random_seed": 42,
        "metrics": {"accuracy": 0.93},
        "result_metadata": {"source": "research-data"},
    }

    created = client.post(f"/api/v1/experiments/{experiment_id}/runs", json=payload)
    listed = client.get(f"/api/v1/experiments/{experiment_id}/runs")

    assert created.status_code == 201
    assert created.json()["experiment_id"] == experiment_id
    assert created.json()["random_seed"] == 42
    assert created.json()["metrics"] == {"accuracy": 0.93}
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["run_id"] == "run-baseline-42"


def test_experiment_run_validation_and_missing_experiment():
    experiment_id = _experiment_id()

    invalid = client.post(
        f"/api/v1/experiments/{experiment_id}/runs",
        json={"random_seed": -1},
    )
    missing = client.post("/api/v1/experiments/missing/runs", json={"random_seed": 42})

    assert invalid.status_code == 422
    assert missing.status_code == 404


def test_create_experiment_run_hides_database_error():
    experiment = Experiment(id="experiment-1", title="Test", user_id="user-1")
    user = User(id="user-1", email="user@example.test", hashed_password="hash", role=UserRole.RESEARCHER)

    class Query:
        def filter(self, *args):
            return self

        def first(self):
            return experiment

    class FailingDatabase:
        rolled_back = False

        def query(self, model):
            assert model is Experiment
            return Query()

        def add(self, item):
            pass

        def commit(self):
            raise SQLAlchemyError("connection password=secret")

        def rollback(self):
            self.rolled_back = True

        def refresh(self, item):
            raise AssertionError("refresh must not run after failed commit")

    db = FailingDatabase()
    try:
        create_experiment_run(
            "experiment-1",
            ExperimentRunCreate(random_seed=42),
            db=db,
            current_user=user,
        )
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail == "Database request failed"
    else:
        raise AssertionError("database failure should be translated to HTTPException")
    assert db.rolled_back is True
