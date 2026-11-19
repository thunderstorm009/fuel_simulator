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

    async def get_incidents(self) -> list[dict[str, Any]]:
        return [{"id": 9, "type": "simulator_unavailable", "severity": "warning"}]


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
