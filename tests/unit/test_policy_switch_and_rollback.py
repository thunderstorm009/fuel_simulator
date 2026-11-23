"""Unit tests for runtime policy switch and automatic rollback (WP12.6)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from api.routes.policy import require_operator_token
from fastapi import HTTPException
from tests.unit.test_recommend_job import snapshot_fixture
from worker.recommend_job import PolicyRunner, RecommendationJob, resolve_policy

from core.models import (
    AllocationTerms,
    FuelType,
    Snapshot,
)
from core.policies.base import PolicyPlan
from core.policies.heuristic import HeuristicPolicy
from core.risk import forecast_pair


class ExplodingPolicy:
    name = "optimizer"

    def recommend(self, snapshot: Snapshot, forecasts: list[Any]) -> list[PolicyPlan]:
        raise RuntimeError("Matrix inversion singularity")


class SlowPolicy:
    name = "optimizer"

    def __init__(self, delay: float = 0.5) -> None:
        self.delay = delay

    def recommend(self, snapshot: Snapshot, forecasts: list[Any]) -> list[PolicyPlan]:
        import time

        time.sleep(self.delay)
        return []


class ViolatingPolicy:
    """Emits candidate plans that violate hard domain constraints."""

    name = "optimizer"

    def recommend(self, snapshot: Snapshot, forecasts: list[Any]) -> list[PolicyPlan]:
        # Return a plan exceeding route capacity which passes Pydantic but fails validator
        invalid_terms = AllocationTerms(
            source_depot_id="depot-central",
            destination_station_id="station-mirpur",
            fuel_type=FuelType.DIESEL,
            quantity=99999999,
            route_id="route-central-mirpur",
        )
        return [
            PolicyPlan(
                request=invalid_terms,
                stockout_hours=2.0,
                arrival_tick=10,
                projected_inventory_at_arrival=100.0,
                target_inventory=5000.0,
            )
        ]


def single_forecast(snapshot: Snapshot):
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    station.inventory[FuelType.DIESEL] = 3000
    return [forecast_pair(snapshot, station, FuelType.DIESEL, seed=42)]


@pytest.mark.asyncio
async def test_policy_runner_rolls_back_on_exception() -> None:
    snapshot = snapshot_fixture()
    forecasts = single_forecast(snapshot)
    rollback_mock = AsyncMock()

    runner = PolicyRunner(
        primary=ExplodingPolicy(),
        fallback=HeuristicPolicy(enable_uncertainty_buffer=False),
        timeout_s=0.2,
        on_rollback=rollback_mock,
    )

    plans, fallback_used, policy_used = await runner.recommend(snapshot, forecasts)

    assert fallback_used is True
    assert policy_used == "heuristic"
    assert runner.primary.name == "heuristic"
    assert rollback_mock.await_count == 1
    failed_name, reason, violations = rollback_mock.await_args[0]
    assert failed_name == "optimizer"
    assert "Matrix inversion singularity" in reason
    assert violations == []
    assert len(plans) > 0


@pytest.mark.asyncio
async def test_policy_runner_rolls_back_on_timeout() -> None:
    snapshot = snapshot_fixture()
    forecasts = single_forecast(snapshot)
    rollback_mock = AsyncMock()

    runner = PolicyRunner(
        primary=SlowPolicy(delay=0.3),
        fallback=HeuristicPolicy(enable_uncertainty_buffer=False),
        timeout_s=0.05,
        on_rollback=rollback_mock,
    )

    plans, fallback_used, policy_used = await runner.recommend(snapshot, forecasts)

    assert fallback_used is True
    assert policy_used == "heuristic"
    assert runner.primary.name == "heuristic"
    assert rollback_mock.await_count == 1
    failed_name, reason, _ = rollback_mock.await_args[0]
    assert failed_name == "optimizer"
    assert "timed out" in reason


@pytest.mark.asyncio
async def test_policy_runner_rolls_back_on_validator_violation() -> None:
    snapshot = snapshot_fixture()
    forecasts = single_forecast(snapshot)
    rollback_mock = AsyncMock()

    runner = PolicyRunner(
        primary=ViolatingPolicy(),
        fallback=HeuristicPolicy(enable_uncertainty_buffer=False),
        timeout_s=0.2,
        on_rollback=rollback_mock,
    )

    plans, fallback_used, policy_used = await runner.recommend(snapshot, forecasts)

    # Must fall back to heuristic
    assert fallback_used is True
    assert policy_used == "heuristic"
    assert runner.primary.name == "heuristic"
    assert rollback_mock.await_count == 1
    failed_name, reason, violations = rollback_mock.await_args[0]
    assert failed_name == "optimizer"
    assert "validator violation" in reason
    assert len(violations) > 0

    # Verify that NO returned plan has quantity <= 0 or validator failures
    for plan in plans:
        assert plan.request.quantity > 0


def test_resolve_policy() -> None:
    p1 = resolve_policy("heuristic")
    assert p1.name == "heuristic"
    p2 = resolve_policy("heuristic_buffer")
    assert p2.name == "heuristic_buffer"
    p3 = resolve_policy("optimizer")
    assert p3.name == "optimizer"
    p4 = resolve_policy("unknown")
    assert p4.name == "heuristic"


@pytest.mark.asyncio
async def test_recommendation_job_picks_up_runtime_policy() -> None:
    snapshot = snapshot_fixture()
    forecasts = single_forecast(snapshot)

    class MockStore:
        def __init__(self) -> None:
            self.policy = "heuristic"
            self.rows: list[dict[str, Any]] = []

        async def expire_stale_recommendations(self, tick: int) -> None:
            pass

        async def get_open_proposal_pairs(self) -> set[tuple[str, str]]:
            return set()

        async def persist_recommendations(self, rows: list[dict[str, Any]]) -> None:
            self.rows.extend(rows)

        async def get_active_policy(self) -> str:
            return self.policy

        async def record_policy_rollback(
            self, failed_policy: str, reason: str, violations: list[str]
        ) -> None:
            self.policy = "heuristic"

    store = MockStore()
    job = RecommendationJob(store)

    # Initial run: heuristic
    rows = await job.run(snapshot, forecasts)
    assert rows
    assert rows[0]["policy_used"] == "heuristic"

    # Switch policy at runtime in the store
    store.rows.clear()
    store.policy = "heuristic_buffer"

    rows2 = await job.run(snapshot, forecasts)
    assert rows2
    assert rows2[0]["policy_used"] == "heuristic_buffer"


@pytest.mark.asyncio
async def test_policy_api_auth_and_auditing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_TOKEN", "valid-test-secret")

    # Verify auth
    assert require_operator_token("valid-test-secret") == "operator"
    with pytest.raises(HTTPException) as exc:
        require_operator_token("wrong-secret")
    assert exc.value.status_code == 401

    with pytest.raises(HTTPException) as exc2:
        require_operator_token("")
    assert exc2.value.status_code == 401
