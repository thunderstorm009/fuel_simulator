"""Integration tests for POST /api/whatif endpoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from api.main import app
from api.routes.read import get_repository
from fastapi.testclient import TestClient

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


class FakeWhatIfRepository:
    def __init__(self) -> None:
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
            "stale": False,
            "data_status": "HEALTHY",
        }
        self.record = {
            "raw_json": raw,
            "fetched_at": datetime.now(timezone.utc),
            "stale": False,
            "data_status": "HEALTHY",
        }
        self.write_count = 0

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        return self.record


@pytest.fixture
def client():
    fake_repo = FakeWhatIfRepository()
    app.dependency_overrides[get_repository] = lambda: fake_repo
    try:
        yield TestClient(app), fake_repo
    finally:
        app.dependency_overrides.clear()


def test_whatif_api_returns_feasible_simulation(client) -> None:
    test_client, fake_repo = client
    payload = {
        "source_depot_id": "depot-dhaka",
        "destination_station_id": "station-mirpur",
        "route_id": "route-dhaka-mirpur",
        "fuel_type": "DIESEL",
        "quantity": 5000.0,
    }

    response = test_client.post("/api/whatif", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["simulated"] is True
    assert "feasible" in data
    assert "verdict" in data
    assert "before" in data
    assert "after" in data
    assert "delta" in data
    assert fake_repo.write_count == 0  # Zero database writes


def test_whatif_api_returns_infeasible_violations(client) -> None:
    test_client, fake_repo = client
    payload = {
        "source_depot_id": "depot-dhaka",
        "destination_station_id": "station-mirpur",
        "route_id": "route-dhaka-mirpur",
        "fuel_type": "DIESEL",
        "quantity": 999999.0,  # Exceeds everything
    }

    response = test_client.post("/api/whatif", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["feasible"] is False
    assert data["verdict"] == "INFEASIBLE"
    assert len(data["violations"]) > 0


def test_whatif_api_invalid_station_returns_422(client) -> None:
    test_client, _ = client
    payload = {
        "source_depot_id": "depot-dhaka",
        "destination_station_id": "station-nonexistent",
        "route_id": "route-dhaka-mirpur",
        "fuel_type": "DIESEL",
        "quantity": 5000.0,
    }

    response = test_client.post("/api/whatif", json=payload)
    assert response.status_code == 422
