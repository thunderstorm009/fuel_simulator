from api.main import app as api_app
from fastapi.testclient import TestClient
from worker.main import app as worker_app

from app.main import app as predictor_app


def test_each_service_exposes_health_and_metrics() -> None:
    for app in (api_app, worker_app, predictor_app):
        client = TestClient(app)
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "service_health_checks_total" in metrics.text
