"""Unit tests for pure what-if allocation simulation."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from core.models import (
    DataStatus,
    Depot,
    DepotStatus,
    FuelType,
    Instance,
    InstanceStatus,
    Metrics,
    Route,
    RouteStatus,
    Snapshot,
    Station,
    StationStatus,
)
from core.what_if import WhatIfCandidate, simulate_what_if


def _build_test_snapshot() -> Snapshot:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    depot = Depot(
        id="depot-dhaka",
        name="Dhaka Central Depot",
        region_id="region-dhaka",
        status=DepotStatus.OPEN,
        capacity={FuelType.DIESEL: 100000.0, FuelType.PETROL: 80000.0, FuelType.OCTANE: 60000.0},
        inventory={FuelType.DIESEL: 40000.0, FuelType.PETROL: 30000.0, FuelType.OCTANE: 20000.0},
        max_daily_dispatch={
            FuelType.DIESEL: 30000.0,
            FuelType.PETROL: 20000.0,
            FuelType.OCTANE: 15000.0,
        },
        dispatch_capacity_per_tick=10000.0,
    )
    station = Station(
        id="station-mirpur",
        name="Mirpur Station",
        region_id="region-dhaka",
        status=StationStatus.OPEN,
        demand_profile="urban_high",
        demand_multiplier=1.0,
        capacity={FuelType.DIESEL: 50000.0, FuelType.PETROL: 40000.0, FuelType.OCTANE: 30000.0},
        inventory={FuelType.DIESEL: 2000.0, FuelType.PETROL: 25000.0, FuelType.OCTANE: 20000.0},
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
        tick=10,
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


def test_what_if_feasible_candidate_improves_metrics() -> None:
    snapshot = _build_test_snapshot()
    candidate = WhatIfCandidate(
        source_depot_id="depot-dhaka",
        destination_station_id="station-mirpur",
        route_id="route-dhaka-mirpur",
        fuel_type=FuelType.DIESEL,
        quantity=8000.0,
    )

    t0 = time.perf_counter()
    res = simulate_what_if(snapshot, candidate)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert res.feasible is True
    assert len(res.violations) == 0
    assert res.verdict == "FEASIBLE_BENEFICIAL"
    assert res.simulated is True
    assert elapsed_ms < 300.0  # Must be fast (< 300 ms)

    # After shipment, stockout is prevented or delayed
    assert res.after.stockout_probability_24h < res.before.stockout_probability_24h
    assert res.after.risk_level == "ok"
    assert res.delta.depot_net_cover_change == -8000.0
    # Original snapshot must not be mutated
    assert len(snapshot.allocations) == 0


def test_what_if_infeasible_candidate_returns_violations() -> None:
    snapshot = _build_test_snapshot()
    # Quantity exceeds route max shipment (10,000L) and depot stock
    candidate = WhatIfCandidate(
        source_depot_id="depot-dhaka",
        destination_station_id="station-mirpur",
        route_id="route-dhaka-mirpur",
        fuel_type=FuelType.DIESEL,
        quantity=95000.0,
    )

    res = simulate_what_if(snapshot, candidate)

    assert res.feasible is False
    assert len(res.violations) > 0
    assert res.verdict == "INFEASIBLE"
