from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import pytest
from worker.store import PostgresStore

from core.models import DataStatus, Forecast, FuelType, Instance, Metrics, RiskLevel, Snapshot
from core.risk import ForecastRecord, TrajectoryPoint


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    @asynccontextmanager
    async def transaction(self):
        yield

    async def fetchval(self, query: str, *args: Any) -> int:
        return 134

    async def fetch(self, query: str) -> list[Any]:
        return []

    async def execute(self, query: str, *args: Any) -> str:
        self.executed.append((query, args))
        return "UPDATE 1"


class FakePool:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    @asynccontextmanager
    async def acquire(self):
        yield self.connection


def snapshot(status: str) -> Snapshot:
    return Snapshot(
        instance=Instance(
            id=1,
            scenario_id="baseline",
            scenario_version="1.0",
            seed=12345,
            sim_time=datetime(2026, 1, 2, 9, 30, tzinfo=timezone.utc),
            tick=134,
            tick_minutes=15,
            status=status,
        ),
        regions=[],
        depots=[],
        stations=[],
        routes=[],
        supply_arrivals=[],
        events=[],
        allocations=[],
        demand_history=[],
        metrics=Metrics(
            served_demand_liters=0,
            unmet_demand_liters=0,
            service_level=1,
            allocation_liters=0,
            allocation_failures=0,
        ),
        fetched_at=datetime.now(timezone.utc),
        stale=False,
        data_status=DataStatus.HEALTHY,
    )


@pytest.mark.asyncio
async def test_same_tick_refresh_replaces_raw_payload_as_well_as_freshness_metadata() -> None:
    connection = FakeConnection()
    store = PostgresStore(FakePool(connection))  # type: ignore[arg-type]

    inserted = await store.insert_snapshot(snapshot("PAUSED"))

    assert inserted is False
    query, args = connection.executed[0]
    assert "raw_json = $" in query
    assert '"status":"PAUSED"' in args[1]
    assert args[0].year == 2026


@pytest.mark.asyncio
async def test_forecast_upsert_replaces_source_after_predictor_recovery() -> None:
    connection = FakeConnection()
    store = PostgresStore(FakePool(connection))  # type: ignore[arg-type]
    forecast = Forecast(
        station_id="station-mirpur",
        fuel_type=FuelType.DIESEL,
        hours_to_stockout=4,
        p10_hours=3,
        p50_hours=4,
        p90_hours=5,
        stockout_probability_24h=0.5,
        confidence=0.9,
        risk_level=RiskLevel.HIGH,
        needs_review=False,
    )
    record = ForecastRecord(forecast, [TrajectoryPoint(0, 100, 90, 110)], {}, source="remote")

    await store.persist_forecasts(snapshot("PAUSED"), [record])

    query, args = next(row for row in connection.executed if "INSERT INTO forecasts" in row[0])
    assert "source = EXCLUDED.source" in query
    assert args[12] == "remote"
