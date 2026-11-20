from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import respx
from api.main import app
from fastapi.testclient import TestClient
from httpx import Response


class HealthRepository:
    def __init__(self, *, database_ok: bool = True, worker_age_s: int = 1, engine_age_s: int = 1):
        now = datetime.now(timezone.utc)
        self.database_ok = database_ok
        self.rows = {
            "worker": {
                "component": "worker",
                "last_seen": now - timedelta(seconds=worker_age_s),
                "detail": {"data_status": "HEALTHY", "breaker_state": "CLOSED"},
            },
            "decision_engine": {
                "component": "decision_engine",
                "last_seen": now - timedelta(seconds=engine_age_s),
                "detail": {"status": "ok"},
            },
        }
        self.snapshot = {
            "fetched_at": now - timedelta(seconds=worker_age_s),
            "stale": False,
            "data_status": "HEALTHY",
        }

    async def check_database(self) -> bool:
        return self.database_ok

    async def get_heartbeat(self, component: str) -> dict[str, Any] | None:
        return self.rows.get(component)

    async def get_latest_snapshot(self) -> dict[str, Any]:
        return self.snapshot


@respx.mock
def test_health_aggregates_components_and_latency(monkeypatch) -> None:
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    respx.get("http://predictor.test/health").mock(
        return_value=Response(200, json={"status": "ok"})
    )
    with TestClient(app) as client:
        app.state.repository = HealthRepository()
        response = client.get("/api/health")

    report = response.json()
    assert report["status"] == "HEALTHY"
    assert report["components"]["predictor"]["status"] == "HEALTHY"
    assert report["components"]["simulator"]["status"] == "HEALTHY"
    assert report["last_check_at"]
    assert report["latency"]["p95_seconds"] >= 0
    assert 0 <= report["latency"]["error_rate"] <= 1


@respx.mock
def test_health_reports_offline_database_and_predictor(monkeypatch) -> None:
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    respx.get("http://predictor.test/health").mock(return_value=Response(503))
    with TestClient(app) as client:
        app.state.repository = HealthRepository(database_ok=False)
        response = client.get("/api/health")

    report = response.json()
    assert report["status"] == "OFFLINE"
    assert report["components"]["database"]["status"] == "OFFLINE"
    assert report["components"]["predictor"]["status"] == "DEGRADED"


@respx.mock
def test_health_marks_stale_worker_and_decision_engine(monkeypatch) -> None:
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    respx.get("http://predictor.test/health").mock(
        return_value=Response(200, json={"status": "ok"})
    )
    with TestClient(app) as client:
        app.state.repository = HealthRepository(worker_age_s=130, engine_age_s=20)
        response = client.get("/api/health")

    report = response.json()
    assert report["status"] == "OFFLINE"
    assert report["components"]["simulator"]["status"] == "OFFLINE"
    assert report["components"]["decision_engine"]["status"] == "DEGRADED"


@respx.mock
def test_stale_decision_engine_degrades_health_without_marking_simulator_offline(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    respx.get("http://predictor.test/health").mock(
        return_value=Response(200, json={"status": "ok"})
    )
    with TestClient(app) as client:
        app.state.repository = HealthRepository(worker_age_s=1, engine_age_s=466)
        response = client.get("/api/health")

    report = response.json()
    assert report["status"] == "DEGRADED"
    assert report["components"]["worker"]["status"] == "HEALTHY"
    assert report["components"]["simulator"]["status"] == "HEALTHY"
    assert report["components"]["decision_engine"]["status"] == "DEGRADED"


@respx.mock
def test_predictor_health_requires_healthy_response_body(monkeypatch) -> None:
    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    respx.get("http://predictor.test/health").mock(
        return_value=Response(200, json={"status": "degraded"})
    )
    with TestClient(app) as client:
        app.state.repository = HealthRepository()
        response = client.get("/api/health")

    assert response.json()["components"]["predictor"]["status"] == "DEGRADED"
