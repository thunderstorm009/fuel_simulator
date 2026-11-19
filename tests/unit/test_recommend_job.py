import json
from pathlib import Path

import pytest
from worker.recommend_job import RecommendationJob

from core.models import FuelType, Snapshot
from core.policies.base import PolicyPlan
from core.policies.heuristic import HeuristicPolicy
from core.risk import forecast_pair

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def snapshot_fixture() -> Snapshot:
    raw = {
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
    raw.update(
        allocations=[],
        demand_history=[],
        fetched_at="2026-01-01T00:00:00Z",
        stale=False,
        data_status="HEALTHY",
    )
    return Snapshot.model_validate(raw)


class MemoryRecommendationStore:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []
        self.expired_at: list[int] = []

    async def expire_stale_recommendations(self, tick: int) -> None:
        self.expired_at.append(tick)
        for row in self.rows:
            if row["status"] == "PROPOSED" and row["expires_tick"] < tick:
                row["status"] = "EXPIRED"

    async def get_open_proposal_pairs(self) -> set[tuple[str, str]]:
        return {
            (str(row["station_id"]), str(row["fuel_type"]))
            for row in self.rows
            if row["status"] in {"PROPOSED", "APPROVED", "SUBMITTED", "IN_TRANSIT"}
        }

    async def persist_recommendations(self, rows: list[dict[str, object]]) -> None:
        self.rows.extend(rows)


class FailingPolicy:
    name = "primary"

    def recommend(self, snapshot: Snapshot, forecasts: list[object]) -> list[PolicyPlan]:
        raise RuntimeError("primary failed")


def forecast_fixture(snapshot: Snapshot):
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    station.inventory[FuelType.DIESEL] = 3000
    return [forecast_pair(snapshot, station, FuelType.DIESEL, seed=42)]


@pytest.mark.asyncio
async def test_job_persists_stable_body_and_dedupes_open_proposals() -> None:
    snapshot = snapshot_fixture()
    store = MemoryRecommendationStore()
    job = RecommendationJob(store, primary=HeuristicPolicy())

    first = await job.run(snapshot, forecast_fixture(snapshot))
    second = await job.run(snapshot, forecast_fixture(snapshot))

    assert first
    assert second == []
    row = store.rows[0]
    assert row["status"] == "PROPOSED"
    assert str(row["idempotency_key"]).startswith("rec-")
    assert row["request_body"]["idempotency_key"] == row["idempotency_key"]
    assert row["request_body"]["quantity"] == row["quantity"]
    assert row["expires_tick"] > row["created_tick"]


@pytest.mark.parametrize("status", ["APPROVED", "SUBMITTED", "IN_TRANSIT"])
@pytest.mark.asyncio
async def test_job_dedupes_recommendations_through_execution_lifecycle(status: str) -> None:
    snapshot = snapshot_fixture()
    store = MemoryRecommendationStore()
    store.rows.append(
        {
            "status": status,
            "station_id": "station-mirpur",
            "fuel_type": "DIESEL",
            "expires_tick": 999,
        }
    )
    job = RecommendationJob(store, primary=HeuristicPolicy())

    rows = await job.run(snapshot, forecast_fixture(snapshot))

    assert rows == []


@pytest.mark.asyncio
async def test_job_falls_back_to_heuristic_and_marks_it() -> None:
    snapshot = snapshot_fixture()
    store = MemoryRecommendationStore()
    job = RecommendationJob(store, primary=FailingPolicy())

    rows = await job.run(snapshot, forecast_fixture(snapshot))

    assert rows
    assert all(row["fallback_used"] is True for row in rows)
    assert all(row["policy_used"] == "heuristic" for row in rows)


@pytest.mark.asyncio
async def test_job_expires_old_proposals_and_skips_stale_snapshots() -> None:
    snapshot = snapshot_fixture()
    snapshot.instance.tick = 20
    store = MemoryRecommendationStore()
    store.rows.append(
        {
            "status": "PROPOSED",
            "station_id": "station-coxsbazar",
            "fuel_type": "PETROL",
            "expires_tick": 10,
        }
    )
    snapshot.stale = True
    job = RecommendationJob(store, primary=HeuristicPolicy())

    rows = await job.run(snapshot, forecast_fixture(snapshot))

    assert rows == []
    assert store.expired_at == [20]
    assert store.rows[0]["status"] == "EXPIRED"
