import json
from pathlib import Path
from typing import Any

import pytest
from worker.forecast_job import ForecastJob

from core.models import Snapshot

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def make_snapshot() -> Snapshot:
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
    raw["fetched_at"] = "2026-01-02T00:00:00Z"
    raw["stale"] = False
    raw["data_status"] = "HEALTHY"
    return Snapshot.model_validate(raw)


class FakeForecastStore:
    def __init__(self) -> None:
        self.rows = []

    async def persist_forecasts(self, snapshot: Snapshot, rows: list[Any]) -> None:
        self.rows.append((snapshot.instance.tick, rows))


@pytest.mark.asyncio
async def test_forecast_job_persists_all_station_fuel_pairs_and_error_metrics() -> None:
    snapshot = make_snapshot()
    store = FakeForecastStore()
    job = ForecastJob(store)

    records = await job.run(snapshot)
    repeated = await job.run(snapshot)

    assert len(records) == 12
    assert store.rows[0][0] == snapshot.instance.tick
    assert len(store.rows[0][1]) == 12
    assert repeated == []
    assert len(store.rows) == 1
    assert {record.forecast.station_id for record in records} == {
        station.id for station in snapshot.stations
    }
    assert all(0 <= record.forecast.confidence <= 1 for record in records)
