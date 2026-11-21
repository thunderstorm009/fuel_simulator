"""Integration tests for GET /api/incidents and incident filtering."""

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


class FakeIncidentsRepo:
    def __init__(self, incidents: list[dict[str, Any]]) -> None:
        self.incidents = incidents
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
        if include_resolved:
            return self.incidents[:limit]
        return [i for i in self.incidents if i.get("resolved_at") is None][:limit]


@pytest.fixture
def api_client():
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_get_incidents_open_and_resolved(api_client: TestClient) -> None:
    sample_incidents = [
        {
            "id": 1,
            "type": "demand_anomaly",
            "severity": "high",
            "detected_at": "2026-01-01T12:00:00Z",
            "resolved_at": None,
            "detail": {"explanation": "Demand surge at Station A", "dedup_key": "k1"},
        },
        {
            "id": 2,
            "type": "bottleneck",
            "severity": "critical",
            "detected_at": "2026-01-01T10:00:00Z",
            "resolved_at": "2026-01-01T11:00:00Z",
            "detail": {"explanation": "Depot dispatch bottleneck", "dedup_key": "k2"},
        },
    ]
    app.dependency_overrides[get_repository] = lambda: FakeIncidentsRepo(sample_incidents)

    # Default is open only
    resp = api_client.get("/api/incidents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["simulated"] is True
    assert body["count"] == 1
    assert body["incidents"][0]["id"] == 1

    # Filter resolved only
    resp_res = api_client.get("/api/incidents?status=resolved")
    assert resp_res.status_code == 200
    body_res = resp_res.json()
    assert body_res["count"] == 1
    assert body_res["incidents"][0]["id"] == 2

    # Filter all
    resp_all = api_client.get("/api/incidents?status=all")
    assert resp_all.status_code == 200
    body_all = resp_all.json()
    assert body_all["count"] == 2
