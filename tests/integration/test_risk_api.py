from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from api.main import app
from api.routes.read import get_repository
from fastapi.testclient import TestClient


class RiskRepository:
    def __init__(self, snapshot: dict[str, Any] | None, forecasts: list[dict[str, Any]]) -> None:
        self.snapshot = snapshot
        self.forecasts = forecasts

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        return self.snapshot

    async def get_incidents(self) -> list[dict[str, Any]]:
        return []

    async def get_latest_forecasts(self) -> list[dict[str, Any]]:
        return self.forecasts

    async def get_forecast_trajectory(
        self, station_id: str, fuel_type: str
    ) -> dict[str, Any] | None:
        return next(
            (
                row
                for row in self.forecasts
                if row["station_id"] == station_id and row["fuel_type"] == fuel_type
            ),
            None,
        )


def snapshot_record() -> dict[str, Any]:
    return {
        "raw_json": {"instance": {"tick": 4}},
        "fetched_at": datetime.now(timezone.utc),
        "stale": False,
        "data_status": "HEALTHY",
    }


def forecast_row() -> dict[str, Any]:
    return {
        "station_id": "station-mirpur",
        "fuel_type": "DIESEL",
        "tick": 4,
        "hours_to_stockout": 5.5,
        "p10": 4.0,
        "p50": 5.5,
        "p90": 7.0,
        "stockout_prob_24h": 0.99,
        "confidence": 0.8,
        "risk_level": "critical",
        "needs_review": False,
        "source": "local",
        "trajectory": [
            {"tick_offset": 0, "mean_inventory": 100, "p10_inventory": 100, "p90_inventory": 100}
        ],
        "drivers": {"demand_multiplier": 1.0, "recent_ratio": 1.1, "arrivals": []},
    }


@pytest.fixture
def api_client():
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_risk_matrix_returns_latest_forecasts(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: RiskRepository(
        snapshot_record(), [forecast_row()]
    )

    response = api_client.get("/api/risks")

    assert response.status_code == 200
    assert response.json()["simulated"] is True
    assert response.json()["forecasts"][0]["risk_level"] == "critical"


def test_trajectory_returns_inventory_band_and_drivers(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: RiskRepository(
        snapshot_record(), [forecast_row()]
    )

    response = api_client.get("/api/risks/station-mirpur/DIESEL/trajectory")

    assert response.status_code == 200
    assert response.json()["trajectory"][0]["p10_inventory"] == 100
    assert response.json()["drivers"]["recent_ratio"] == 1.1


def test_risks_returns_503_only_when_snapshot_is_absent(api_client: TestClient) -> None:
    app.dependency_overrides[get_repository] = lambda: RiskRepository(None, [])

    response = api_client.get("/api/risks")

    assert response.status_code == 503
