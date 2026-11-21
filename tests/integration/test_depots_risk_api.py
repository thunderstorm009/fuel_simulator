"""Integration tests for GET /api/depots/risk."""

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


class FakeDepotRiskRepo:
    def __init__(self, risks: list[dict[str, Any]]) -> None:
        self.risks = risks
        self.snapshot = {
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

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        return {
            "raw_json": self.snapshot,
            "fetched_at": datetime.now(timezone.utc),
            "stale": False,
            "data_status": "HEALTHY",
        }

    async def get_incidents(
        self, include_resolved: bool = False, limit: int = 100
    ) -> list[dict[str, Any]]:
        return []

    async def get_depot_risks(self) -> list[dict[str, Any]]:
        return self.risks


@pytest.fixture
def api_client():
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_get_depots_risk_returns_projections(api_client: TestClient) -> None:
    sample_risks = [
        {
            "depot_id": "depot_dhaka",
            "fuel_type": "DIESEL",
            "tick": 10,
            "current_inventory": 45000.0,
            "scheduled_arrivals": 20000.0,
            "committed_allocations": 5000.0,
            "projected_demand": 30000.0,
            "net_cover_liters": 30000.0,
            "cover_hours": 36.0,
            "is_bottleneck": False,
            "dispatch_utilization": 0.35,
            "evidence": {"reachable_stations_count": 3},
        }
    ]
    app.dependency_overrides[get_repository] = lambda: FakeDepotRiskRepo(sample_risks)

    resp = api_client.get("/api/depots/risk")
    assert resp.status_code == 200
    body = resp.json()
    assert body["simulated"] is True
    assert body["count"] == 1
    assert body["depot_risks"][0]["depot_id"] == "depot_dhaka"
    assert body["depot_risks"][0]["net_cover_liters"] == 30000.0
