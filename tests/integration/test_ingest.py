from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from worker.ingest import SnapshotIngestor

from core.models import (
    Allocation,
    DataStatus,
    DemandObs,
    Depot,
    Instance,
    Metrics,
    Region,
    Route,
    SimEvent,
    Snapshot,
    Station,
    SupplyArrival,
)
from core.sim_client import SimResult, SimUnavailable

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


class AttributeMapping(dict[str, Any]):
    def __getattr__(self, name: str) -> Any:
        return self[name]


def sample(name: str) -> Any:
    return json.loads((SAMPLES / f"{name}.json").read_text())


class FakeClient:
    def __init__(self) -> None:
        self.stale = False
        self.failure_method: str | None = None
        self.malformed_stations: list[Any] | None = None
        self.history_limits: list[tuple[str | None, int]] = []
        self.breaker = SimpleNamespace(state=SimpleNamespace(value="closed"))
        self.tick = 0

    async def _result(self, method: str, value: Any) -> SimResult[Any]:
        if self.failure_method == method:
            raise SimUnavailable("temporary simulator failure")
        return SimResult(value, self.stale)

    async def get_instance(self) -> SimResult[Any]:
        instance = Instance.model_validate(sample("instance")).model_copy(
            update={"tick": self.tick}
        )
        return await self._result("get_instance", instance)

    async def get_regions(self) -> SimResult[Any]:
        return await self._result(
            "get_regions", [Region.model_validate(x) for x in sample("regions")]
        )

    async def get_depots(self) -> SimResult[Any]:
        return await self._result("get_depots", [Depot.model_validate(x) for x in sample("depots")])

    async def get_stations(self) -> SimResult[Any]:
        if self.malformed_stations is not None:
            return await self._result("get_stations", self.malformed_stations)
        return await self._result(
            "get_stations", [Station.model_validate(x) for x in sample("stations")]
        )

    async def get_routes(self) -> SimResult[Any]:
        return await self._result("get_routes", [Route.model_validate(x) for x in sample("routes")])

    async def get_supply_arrivals(self) -> SimResult[Any]:
        return await self._result(
            "get_supply_arrivals",
            [SupplyArrival.model_validate(x) for x in sample("supply-arrivals")],
        )

    async def get_events(self) -> SimResult[Any]:
        return await self._result(
            "get_events", [SimEvent.model_validate(x) for x in sample("events")]
        )

    async def get_allocations(self) -> SimResult[Any]:
        return await self._result(
            "get_allocations", [Allocation.model_validate(x) for x in sample("allocations")]
        )

    async def get_metrics(self) -> SimResult[Any]:
        return await self._result("get_metrics", Metrics.model_validate(sample("metrics")))

    async def get_demand_history(
        self, station_id: str | None = None, *, limit: int = 100
    ) -> SimResult[Any]:
        self.history_limits.append((station_id, limit))
        rows = [row for row in sample("demand-history") if row["station_id"] == station_id]
        return await self._result(
            "get_demand_history", [DemandObs.model_validate(x) for x in rows[:limit]]
        )


class FakeStore:
    def __init__(self) -> None:
        self.snapshots: list[Snapshot] = []
        self.events: list[dict[str, Any]] = []
        self.heartbeats = 0
        self.prunes = 0
        self.latest_status: str | None = None

    async def insert_snapshot(self, snapshot: Snapshot) -> bool:
        self.latest_status = snapshot.data_status.value
        if self.snapshots and self.snapshots[-1].instance.tick == snapshot.instance.tick:
            return False
        self.snapshots.append(snapshot)
        return True

    async def record_integration_event(self, kind: str, detail: dict[str, Any]) -> None:
        self.events.append({"kind": kind, **detail})

    async def mark_latest_degraded(self) -> None:
        self.latest_status = "DEGRADED"

    async def heartbeat(self, component: str, detail: dict[str, Any]) -> None:
        self.heartbeats += 1

    async def prune_snapshots(self, keep: int = 1000) -> None:
        self.prunes += 1


@pytest.mark.asyncio
async def test_ingest_builds_one_snapshot_and_limits_each_history_request() -> None:
    client = FakeClient()
    store = FakeStore()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ingestor = SnapshotIngestor(client, store, now=lambda: now)

    inserted = await ingestor.run_once()

    assert inserted is True
    snapshot = store.snapshots[0]
    assert isinstance(snapshot, Snapshot)
    assert snapshot.data_status is DataStatus.HEALTHY
    assert len(snapshot.demand_history) > 0
    assert len(client.history_limits) == 4
    assert all(limit == 100 for _, limit in client.history_limits)
    assert store.heartbeats == 1
    assert store.prunes == 1


@pytest.mark.asyncio
async def test_unchanged_tick_is_not_inserted_twice() -> None:
    store = FakeStore()
    ingestor = SnapshotIngestor(
        FakeClient(), store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )

    assert await ingestor.run_once() is True
    assert await ingestor.run_once() is False
    assert len(store.snapshots) == 1


@pytest.mark.asyncio
async def test_successful_unchanged_snapshot_reaches_forecast_deduplicator() -> None:
    store = FakeStore()
    calls: list[int] = []

    async def on_snapshot(snapshot: Snapshot) -> None:
        calls.append(snapshot.instance.tick)

    ingestor = SnapshotIngestor(
        FakeClient(),
        store,
        now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        on_snapshot=on_snapshot,
    )

    assert await ingestor.run_once() is True
    assert await ingestor.run_once() is False
    assert calls == [0, 0]


@pytest.mark.asyncio
async def test_simulator_reset_can_reuse_a_previously_seen_tick() -> None:
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(
        client, store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )

    assert await ingestor.run_once() is True
    client.tick = 1
    assert await ingestor.run_once() is True
    client.tick = 0
    assert await ingestor.run_once() is True
    assert [row.instance.tick for row in store.snapshots] == [0, 1, 0]


@pytest.mark.asyncio
async def test_stale_response_marks_snapshot_degraded() -> None:
    client = FakeClient()
    client.stale = True
    store = FakeStore()
    ingestor = SnapshotIngestor(
        client, store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )

    await ingestor.run_once()

    assert store.snapshots[0].stale is True
    assert store.snapshots[0].data_status is DataStatus.DEGRADED


@pytest.mark.asyncio
async def test_partial_fetch_failure_keeps_last_good_snapshot_and_logs_event() -> None:
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(
        client, store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    await ingestor.run_once()
    last_good = store.snapshots[0]
    client.failure_method = "get_routes"

    inserted = await ingestor.run_once()

    assert inserted is False
    assert store.snapshots == [last_good]
    assert store.latest_status == "DEGRADED"
    assert store.events[-1]["kind"] == "snapshot_rejected"


@pytest.mark.asyncio
async def test_successful_unchanged_tick_clears_degraded_status_without_duplicate() -> None:
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(
        client, store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    await ingestor.run_once()
    client.failure_method = "get_routes"
    await ingestor.run_once()
    client.failure_method = None

    inserted = await ingestor.run_once()

    assert inserted is False
    assert len(store.snapshots) == 1
    assert store.latest_status == "HEALTHY"


@pytest.mark.asyncio
async def test_missing_station_field_is_rejected_and_keeps_last_snapshot(caplog) -> None:
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(
        client, store, now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    await ingestor.run_once()
    last_good = store.snapshots[0]
    client.malformed_stations = [AttributeMapping(id="station-mirpur")]

    inserted = await ingestor.run_once()

    assert inserted is False
    assert store.snapshots == [last_good]
    assert store.events[-1]["kind"] == "snapshot_rejected"
    assert store.events[-1]["error_type"] == "ValidationError"
    assert '"event": "snapshot_rejected"' in caplog.text
