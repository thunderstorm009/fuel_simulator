from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx
import pytest
from worker.forecast_job import ForecastJob
from worker.forecaster import RemoteForecaster, RemoteForecastError

from core.models import FuelType, Snapshot

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
        self.predictor_incidents: list[tuple[bool, str | None]] = []

    async def persist_forecasts(self, snapshot: Snapshot, rows: list[Any]) -> None:
        self.rows.append((snapshot.instance.tick, rows))

    async def set_predictor_incident(self, active: bool, reason: str | None = None) -> None:
        self.predictor_incidents.append((active, reason))


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


@pytest.mark.asyncio
async def test_predictor_failure_uses_low_confidence_baseline_and_opens_incident() -> None:
    async def unavailable(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "temporarily unavailable"})

    snapshot = make_snapshot()
    store = FakeForecastStore()
    remote = RemoteForecaster(
        "http://predictor",
        failure_threshold=1,
        transport=httpx.MockTransport(unavailable),
    )
    try:
        records = await ForecastJob(store, forecaster=remote).run(snapshot)
    finally:
        await remote.close()

    assert len(records) == 12
    assert all(record.source == "baseline" for record in records)
    assert all(record.forecast.needs_review for record in records)
    assert all(record.forecast.confidence <= 0.4 for record in records)
    assert store.predictor_incidents[0] == (True, "predictor_5xx")


@pytest.mark.asyncio
async def test_predictor_breaker_allows_only_one_half_open_probe(monkeypatch) -> None:
    from core.risk import forecast_pair

    snapshot = make_snapshot()
    station = snapshot.stations[0]
    record = forecast_pair(snapshot, station, FuelType.DIESEL, seed=3)
    calls = 0
    release = asyncio.Event()
    entered = asyncio.Event()

    async def transport(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503)
        if calls > 2:
            return httpx.Response(
                200,
                json={
                    "forecast": record.forecast.model_dump(mode="json"),
                    "trajectory": [asdict(point) for point in record.trajectory],
                    "drivers": record.drivers,
                    "source": "remote",
                },
            )
        entered.set()
        await release.wait()
        return httpx.Response(
            200,
            json={
                "forecast": record.forecast.model_dump(mode="json"),
                "trajectory": [asdict(point) for point in record.trajectory],
                "drivers": record.drivers,
                "source": "remote",
            },
        )

    now = [0.0]
    monkeypatch.setattr("worker.forecaster.time.monotonic", lambda: now[0])
    remote = RemoteForecaster(
        "http://predictor",
        failure_threshold=1,
        reset_after_s=10,
        transport=httpx.MockTransport(transport),
    )
    try:
        with pytest.raises(RemoteForecastError, match="predictor_5xx"):
            await remote.forecast(snapshot, station, record.forecast.fuel_type, 3)
        now[0] = 11.0
        probe = asyncio.create_task(
            remote.forecast(snapshot, station, record.forecast.fuel_type, 3)
        )
        await entered.wait()
        with pytest.raises(RemoteForecastError, match="breaker_open"):
            await remote.forecast(snapshot, station, record.forecast.fuel_type, 3)
        release.set()
        assert (await probe).source == "remote"
    finally:
        release.set()
        await remote.close()

    assert calls == 2
