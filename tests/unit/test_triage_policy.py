"""Unit tests for constrained-supply triage and event-aware policy behavior."""

from __future__ import annotations

import json
from pathlib import Path

from core.models import (
    DepotStatus,
    Forecast,
    FuelType,
    RiskLevel,
    Snapshot,
    StationStatus,
)
from core.policies.heuristic import HeuristicPolicy
from core.risk import ForecastRecord, TrajectoryPoint

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


def make_forecast(
    station_id: str,
    fuel: FuelType,
    *,
    hours_to_stockout: float,
    current_inventory: float,
    burn_rate_per_tick: float = 50.0,
) -> ForecastRecord:
    trajectory = [
        TrajectoryPoint(
            offset,
            max(0.0, current_inventory - burn_rate_per_tick * offset),
            max(0.0, current_inventory - burn_rate_per_tick * offset),
            max(0.0, current_inventory - burn_rate_per_tick * offset),
        )
        for offset in range(97)
    ]
    forecast = Forecast(
        station_id=station_id,
        fuel_type=fuel,
        hours_to_stockout=hours_to_stockout,
        p10_hours=max(0.5, hours_to_stockout - 1.0),
        p50_hours=hours_to_stockout,
        p90_hours=hours_to_stockout + 1.0,
        stockout_probability_24h=0.95 if hours_to_stockout < 12 else 0.6,
        confidence=0.85,
        risk_level=RiskLevel.CRITICAL if hours_to_stockout < 8 else RiskLevel.HIGH,
        needs_review=False,
    )
    return ForecastRecord(
        forecast=forecast,
        trajectory=trajectory,
        drivers={"demand_multiplier": 1.0, "recent_ratio": 1.0},
    )


def test_station_outage_never_receives_recommendations() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(s for s in snapshot.stations if s.id == "station-mirpur")
    mirpur.status = StationStatus.OUTAGE
    mirpur.inventory[FuelType.DIESEL] = 500.0

    forecast = make_forecast(
        "station-mirpur", FuelType.DIESEL, hours_to_stockout=1.0, current_inventory=500.0
    )
    policy = HeuristicPolicy()
    plans = policy.recommend(snapshot, [forecast])

    assert len(plans) == 0, "Station in OUTAGE must never receive allocation recommendations"


def test_constrained_depot_is_shippable_but_deprioritized_behind_open() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(s for s in snapshot.stations if s.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 2000.0

    depot_gazipur = next(d for d in snapshot.depots if d.id == "depot-gazipur")
    depot_patiya = next(d for d in snapshot.depots if d.id == "depot-patiya")
    depot_gazipur.status = DepotStatus.CONSTRAINED
    depot_patiya.status = DepotStatus.OPEN
    depot_gazipur.inventory[FuelType.DIESEL] = 20000.0
    depot_patiya.inventory[FuelType.DIESEL] = 20000.0

    route_gazipur = next(
        r
        for r in snapshot.routes
        if r.source_depot_id == "depot-gazipur" and r.destination_station_id == "station-mirpur"
    )
    route_patiya = next(
        r
        for r in snapshot.routes
        if r.source_depot_id == "depot-patiya" and r.destination_station_id == "station-mirpur"
    )
    route_patiya.transit_ticks = route_gazipur.transit_ticks

    forecast = make_forecast(
        "station-mirpur", FuelType.DIESEL, hours_to_stockout=4.0, current_inventory=2000.0
    )
    policy = HeuristicPolicy()
    plans = policy.recommend(snapshot, [forecast])

    assert len(plans) >= 1
    assert plans[0].request.source_depot_id == "depot-patiya"


def test_two_pass_triage_under_scarce_depot_stock() -> None:
    """When depot inventory is scarce, pass 1 covers 12h emergency needs for all at-risk stations.

    Pass 2 allocates remaining stock up to target. Total allocations never exceed depot stock.
    """
    snapshot = snapshot_fixture()
    mirpur = next(s for s in snapshot.stations if s.id == "station-mirpur")
    tongi = next(s for s in snapshot.stations if s.id == "station-tongi")

    mirpur.inventory[FuelType.DIESEL] = 1000.0
    tongi.inventory[FuelType.DIESEL] = 2000.0

    depot = next(d for d in snapshot.depots if d.id == "depot-gazipur")
    depot.inventory[FuelType.DIESEL] = 5000.0
    depot.dispatch_capacity_per_tick = 10000.0

    for r in snapshot.routes:
        if r.source_depot_id != "depot-gazipur":
            r.status = "DISRUPTED"

    fc_mirpur = make_forecast(
        "station-mirpur", FuelType.DIESEL, hours_to_stockout=2.0, current_inventory=1000.0
    )
    fc_tongi = make_forecast(
        "station-tongi", FuelType.DIESEL, hours_to_stockout=6.0, current_inventory=2000.0
    )

    policy = HeuristicPolicy()
    plans = policy.recommend(snapshot, [fc_mirpur, fc_tongi])

    assert len(plans) >= 1
    total_allocated = sum(p.request.quantity for p in plans)
    assert total_allocated <= 5000.0, f"Total allocated {total_allocated} exceeded depot stock 5000"

    destinations = {p.request.destination_station_id for p in plans}
    assert "station-mirpur" in destinations
    assert "station-tongi" in destinations

    for p in plans:
        assert hasattr(p, "triage") or "triage" in p.constraints_applied
        if p.triage:
            assert "priority_rule" in p.triage


def test_triage_reservations_carry_across_passes() -> None:
    """Pass 1 plus pass 2 together never exceed depot stock, dispatch, or station capacity."""
    snapshot = snapshot_fixture()
    mirpur = next(s for s in snapshot.stations if s.id == "station-mirpur")
    tongi = next(s for s in snapshot.stations if s.id == "station-tongi")

    mirpur.inventory[FuelType.DIESEL] = 500.0
    tongi.inventory[FuelType.DIESEL] = 800.0

    depot = next(d for d in snapshot.depots if d.id == "depot-gazipur")
    depot.inventory[FuelType.DIESEL] = 4000.0
    depot.dispatch_capacity_per_tick = 3500.0

    for r in snapshot.routes:
        if r.source_depot_id != "depot-gazipur":
            r.status = "DISRUPTED"

    fc_mirpur = make_forecast(
        "station-mirpur", FuelType.DIESEL, hours_to_stockout=1.5, current_inventory=500.0
    )
    fc_tongi = make_forecast(
        "station-tongi", FuelType.DIESEL, hours_to_stockout=3.0, current_inventory=800.0
    )

    policy = HeuristicPolicy()
    plans = policy.recommend(snapshot, [fc_mirpur, fc_tongi])

    total_allocated = sum(p.request.quantity for p in plans)
    assert total_allocated <= depot.dispatch_capacity_per_tick
    assert total_allocated <= depot.inventory[FuelType.DIESEL]

    for p in plans:
        st = next(s for s in snapshot.stations if s.id == p.request.destination_station_id)
        assert (
            st.inventory[p.request.fuel_type] + p.request.quantity
            <= st.capacity[p.request.fuel_type]
        )
