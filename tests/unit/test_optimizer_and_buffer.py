"""Unit tests for uncertainty-aware allocation buffer and linear flow optimizer."""

from __future__ import annotations

from datetime import datetime, timezone

from core.models import (
    DataStatus,
    Depot,
    DepotStatus,
    Forecast,
    FuelType,
    Instance,
    InstanceStatus,
    Metrics,
    RiskLevel,
    Route,
    RouteStatus,
    Snapshot,
    Station,
    StationStatus,
)
from core.policies.heuristic import HeuristicPolicy
from core.policies.optimizer import OptimizerPolicy
from core.risk import ForecastRecord
from core.validator import validate


def _build_snapshot() -> Snapshot:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    depot = Depot(
        id="depot-dhaka",
        name="Dhaka Depot",
        region_id="region-dhaka",
        status=DepotStatus.OPEN,
        capacity={FuelType.DIESEL: 100000.0, FuelType.PETROL: 80000.0, FuelType.OCTANE: 60000.0},
        inventory={FuelType.DIESEL: 50000.0, FuelType.PETROL: 40000.0, FuelType.OCTANE: 30000.0},
        max_daily_dispatch={
            FuelType.DIESEL: 40000.0,
            FuelType.PETROL: 30000.0,
            FuelType.OCTANE: 20000.0,
        },
        dispatch_capacity_per_tick=15000.0,
    )
    station = Station(
        id="station-mirpur",
        name="Mirpur Station",
        region_id="region-dhaka",
        status=StationStatus.OPEN,
        demand_profile="urban_high",
        demand_multiplier=1.0,
        capacity={FuelType.DIESEL: 50000.0, FuelType.PETROL: 40000.0, FuelType.OCTANE: 30000.0},
        inventory={FuelType.DIESEL: 3000.0, FuelType.PETROL: 20000.0, FuelType.OCTANE: 15000.0},
    )
    route = Route(
        id="route-dhaka-mirpur",
        source_depot_id="depot-dhaka",
        destination_station_id="station-mirpur",
        transit_ticks=4,
        max_shipment=10000.0,
        status=RouteStatus.AVAILABLE,
    )
    inst = Instance(
        id=1,
        scenario_id="baseline",
        scenario_version="1.0",
        tick=1,
        sim_time=sim_time,
        status=InstanceStatus.RUNNING,
        tick_minutes=15,
        speed=1.0,
        seed=42,
    )
    return Snapshot(
        instance=inst,
        regions=[],
        depots=[depot],
        stations=[station],
        routes=[route],
        supply_arrivals=[],
        events=[],
        allocations=[],
        demand_history=[],
        metrics=Metrics(
            served_demand_liters=1000.0,
            unmet_demand_liters=0.0,
            service_level=1.0,
            allocation_liters=0.0,
            allocation_failures=0,
        ),
        fetched_at=sim_time,
        stale=False,
        data_status=DataStatus.HEALTHY,
    )


def test_heuristic_with_uncertainty_buffer() -> None:
    snapshot = _build_snapshot()
    # High risk, low confidence (< 0.65)
    forecast = Forecast(
        station_id="station-mirpur",
        fuel_type=FuelType.DIESEL,
        hours_to_stockout=4.0,
        p10_hours=2.0,
        p50_hours=4.0,
        p90_hours=6.0,
        stockout_probability_24h=0.85,
        confidence=0.55,
        risk_level=RiskLevel.HIGH,
        needs_review=False,
    )
    record = ForecastRecord(
        forecast=forecast,
        trajectory=[],
        drivers={"demand_multiplier": 1.0, "recent_ratio": 1.0},
    )

    policy_with_buffer = HeuristicPolicy(enable_uncertainty_buffer=True)
    policy_without_buffer = HeuristicPolicy(enable_uncertainty_buffer=False)

    plans_buf = policy_with_buffer.recommend(snapshot, [record])
    plans_no_buf = policy_without_buffer.recommend(snapshot, [record])

    assert len(plans_buf) > 0
    assert len(plans_no_buf) > 0

    # With safety buffer enabled, requested and allocated quantity accounts for P90 variance
    assert plans_buf[0].triage["safety_buffer_liters"] > 0
    assert plans_buf[0].request.quantity >= plans_no_buf[0].request.quantity
    # Must pass constraint validator
    assert len(validate(plans_buf[0].request, snapshot)) == 0


def test_optimizer_policy_satisfies_all_constraints() -> None:
    snapshot = _build_snapshot()
    forecast = Forecast(
        station_id="station-mirpur",
        fuel_type=FuelType.DIESEL,
        hours_to_stockout=3.0,
        p10_hours=1.5,
        p50_hours=3.0,
        p90_hours=5.0,
        stockout_probability_24h=0.90,
        confidence=0.85,
        risk_level=RiskLevel.CRITICAL,
        needs_review=False,
    )
    record = ForecastRecord(
        forecast=forecast,
        trajectory=[],
        drivers={"demand_multiplier": 1.0, "recent_ratio": 1.0},
    )

    optimizer = OptimizerPolicy()
    plans = optimizer.recommend(snapshot, [record])

    assert len(plans) > 0
    for plan in plans:
        violations = validate(plan.request, snapshot)
        assert len(violations) == 0
        assert plan.request.quantity <= 10000.0  # Route max shipment
        assert plan.request.source_depot_id == "depot-dhaka"
