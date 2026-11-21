from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from api.main import app
from api.routes.read import get_repository
from fastapi.testclient import TestClient

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


class FakeRepository:
    def __init__(self, snapshot: dict[str, Any] | None) -> None:
        self.snapshot = snapshot

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        return self.snapshot

    async def get_incidents(
        self, include_resolved: bool = True, limit: int = 100
    ) -> list[dict[str, Any]]:
        return [{"id": 9, "type": "simulator_unavailable", "severity": "warning"}]

    async def get_incident(self, incident_id: int) -> dict[str, Any] | None:
        if incident_id == 9:
            return {
                "id": 9,
                "type": "simulator_unavailable",
                "severity": "warning",
                "detected_at": "2026-11-21T10:00:00Z",
                "resolved_at": None,
                "detail": {"explanation": "Simulator connection dropped", "entity_id": "sim-1"},
            }
        return None


def seeded_record(age_seconds: int = 0, stale: bool = False) -> dict[str, Any]:
    raw = {
        "instance": json.loads((SAMPLES / "instance.json").read_text()),
        "regions": json.loads((SAMPLES / "regions.json").read_text()),
        "depots": json.loads((SAMPLES / "depots.json").read_text()),
        "stations": json.loads((SAMPLES / "stations.json").read_text()),
        "routes": json.loads((SAMPLES / "routes.json").read_text()),
        "supply_arrivals": json.loads((SAMPLES / "supply-arrivals.json").read_text()),
        "events": json.loads((SAMPLES / "events.json").read_text()),
        "allocations": json.loads((SAMPLES / "allocations.json").read_text()),
        "demand_history": [],
        "metrics": json.loads((SAMPLES / "metrics.json").read_text()),
        "stale": stale,
        "data_status": "HEALTHY",
    }
    return {
        "raw_json": raw,
        "fetched_at": datetime.now(timezone.utc) - timedelta(seconds=age_seconds),
        "stale": stale,
        "data_status": "HEALTHY",
    }


@pytest.fixture
def api_client():
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_state_and_data_health_read_latest_snapshot(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(seeded_record())

    response = api_client.get("/api/state")
    health = api_client.get("/api/data-health")

    assert response.status_code == 200
    assert response.json()["simulated"] is True
    assert response.json()["data_status"] == "HEALTHY"
    assert response.json()["data_age_seconds"] < 15
    assert response.json()["model_version"] == "1.1.0"
    assert response.json()["policy_version"] == "2.1.0"
    assert health.json()["data_status"] == "HEALTHY"


def test_stale_snapshot_returns_200_with_degraded_status(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(
        seeded_record(age_seconds=35, stale=True)
    )

    response = api_client.get("/api/state")

    assert response.status_code == 200
    assert response.json()["stale"] is True
    assert response.json()["data_status"] == "DEGRADED"
    assert response.json()["data_age_seconds"] >= 35


def test_very_old_snapshot_stays_available_as_offline_data(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(
        seeded_record(age_seconds=130)
    )

    response = api_client.get("/api/state")

    assert response.status_code == 200
    assert response.json()["data_status"] == "OFFLINE"


def test_read_endpoints_return_503_without_any_snapshot(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(None)

    for path in ("/api/state", "/api/data-health", "/api/events", "/api/metrics-summary"):
        assert api_client.get(path).status_code == 503


def test_events_and_metrics_summary_include_simulator_data_and_incidents(
    api_client: TestClient,
) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(seeded_record())

    events = api_client.get("/api/events").json()
    metrics = api_client.get("/api/metrics-summary").json()

    assert events["simulated"] is True
    assert events["incidents"][0]["type"] == "simulator_unavailable"
    assert metrics["metrics"]["service_level"] >= 0


def test_regional_demand_and_evaluation_endpoints(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(seeded_record())

    reg = api_client.get("/api/regional-demand")
    assert reg.status_code == 200
    reg_data = reg.json()
    assert reg_data["simulated"] is True
    assert "regional_demand" in reg_data

    eval_res = api_client.get("/api/evaluation/summary")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["simulated"] is True
    assert eval_data["evaluation_type"] == "offline_benchmark"
    assert "backtest" in eval_data


def test_incident_summary_endpoint(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: FakeRepository(seeded_record())

    # Found incident
    res = api_client.get("/api/incidents/9/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == 9
    assert data["simulated"] is True
    assert data["label"] == "AI-generated summary of simulated data"
    assert "summary" in data
    assert len(data["summary"]) > 0

    # Not found incident
    not_found = api_client.get("/api/incidents/999/summary")
    assert not_found.status_code == 404


def test_version_endpoint(api_client: TestClient) -> None:
    res = api_client.get("/api/version")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated"] is True
    assert "git_sha" in data
    assert "tag" in data
    assert "model_version" in data
    assert "policy_version" in data
    assert "build_time" in data
