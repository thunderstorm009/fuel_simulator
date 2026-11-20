import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from core.models import Snapshot

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def sample_snapshot() -> Snapshot:
    raw: dict[str, Any] = {
        name: json.loads((SAMPLES / f"{name}.json").read_text())
        for name in (
            "instance",
            "regions",
            "depots",
            "stations",
            "routes",
            "supply-arrivals",
            "events",
            "metrics",
        )
    }
    raw["supply_arrivals"] = raw.pop("supply-arrivals")
    raw["allocations"] = []
    raw["demand_history"] = json.loads((SAMPLES / "demand-history-96-ticks.json").read_text())
    raw.update(fetched_at="2026-01-02T00:00:00Z", stale=False, data_status="HEALTHY")
    return Snapshot.model_validate(raw)


def test_predictor_endpoint_returns_valid_forecast_and_trajectory() -> None:
    snapshot = sample_snapshot()
    station = snapshot.stations[0]

    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "snapshot": snapshot.model_dump(mode="json"),
                "station_id": station.id,
                "fuel_type": "DIESEL",
                "seed": 17,
            },
        )

    assert response.status_code == 200
    result = response.json()
    assert result["forecast"]["station_id"] == station.id
    assert result["forecast"]["fuel_type"] == "DIESEL"
    assert result["trajectory"]
    assert result["source"] == "remote"


def test_predictor_rejects_unknown_station() -> None:
    snapshot = sample_snapshot()
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "snapshot": snapshot.model_dump(mode="json"),
                "station_id": "station-missing",
                "fuel_type": "DIESEL",
                "seed": 17,
            },
        )
    assert response.status_code == 404


def test_predictor_failure_switch_requires_operator_token(monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_TOKEN", "test-operator")
    with TestClient(app) as client:
        denied = client.post("/admin/fail", json={"enabled": True})
        enabled = client.post(
            "/admin/fail",
            json={"enabled": True},
            headers={"X-Operator-Token": "test-operator"},
        )
        failed = client.post(
            "/predict",
            json={
                "snapshot": sample_snapshot().model_dump(mode="json"),
                "station_id": "station-mirpur",
                "fuel_type": "DIESEL",
                "seed": 17,
            },
        )
        client.post(
            "/admin/fail",
            json={"enabled": False},
            headers={"X-Operator-Token": "test-operator"},
        )
    assert denied.status_code == 401
    assert enabled.json() == {"enabled": True}
    assert failed.status_code == 503
