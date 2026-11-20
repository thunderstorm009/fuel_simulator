from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import pytest
from worker.store import PostgresStore

from core.models import DataStatus, Instance, Metrics, Snapshot


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    @asynccontextmanager
    async def transaction(self):
        yield

    async def fetchval(self, query: str) -> int:
        return 134

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
