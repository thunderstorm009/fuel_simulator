"""Unit tests for pure depot and network supply risk projections."""

from __future__ import annotations

import json
from pathlib import Path

from core.depot_risk import calculate_depot_risks
from core.models import FuelType, Snapshot, SupplyArrival, SupplyArrivalStatus

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def base_snapshot() -> Snapshot:
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


def test_calculate_depot_risks_baseline():
    """Baseline snapshot calculates risks for every depot and 3 fuel types."""
    snapshot = base_snapshot()
    risks = calculate_depot_risks(snapshot, horizon_hours=24.0)

    expected_count = len(snapshot.depots) * 3
    assert len(risks) == expected_count

    for r in risks:
        assert r.current_inventory >= 0
        assert r.scheduled_arrivals >= 0
        assert r.committed_allocations >= 0
        assert r.projected_demand >= 0
        assert isinstance(r.is_bottleneck, bool)
        assert r.cover_hours >= 0


def test_shipment_delay_moves_cover_curve():
    """Delaying an arrival past 24h horizon reduces scheduled arrivals and net cover."""
    snapshot = base_snapshot()
    depot_id = snapshot.depots[0].id
    fuel = FuelType.DIESEL

    # Baseline risk
    base_risks = {
        (r.depot_id, r.fuel_type): r for r in calculate_depot_risks(snapshot, horizon_hours=24.0)
    }
    base_target = base_risks[(depot_id, fuel.value)]

    # Add a scheduled arrival at tick 20 (within 24h horizon of 96 ticks)
    arrival = SupplyArrival(
        id="arr-test-1",
        depot_id=depot_id,
        fuel_type=fuel,
        quantity=5000.0,
        planned_tick=20,
        actual_tick=None,
        status=SupplyArrivalStatus.SCHEDULED,
    )
    snap_with_arr = snapshot.model_copy(
        update={"supply_arrivals": list(snapshot.supply_arrivals) + [arrival]}
    )
    with_arr_risks = {
        (r.depot_id, r.fuel_type): r
        for r in calculate_depot_risks(snap_with_arr, horizon_hours=24.0)
    }
    target_with_arr = with_arr_risks[(depot_id, fuel.value)]
    assert target_with_arr.scheduled_arrivals == base_target.scheduled_arrivals + 5000.0
    assert target_with_arr.net_cover_liters == base_target.net_cover_liters + 5000.0

    # Delay the arrival to tick 150 (outside 24h horizon of 96 ticks)
    delayed_arrival = arrival.model_copy(
        update={"planned_tick": 150, "status": SupplyArrivalStatus.DELAYED}
    )
    snap_delayed = snapshot.model_copy(
        update={"supply_arrivals": list(snapshot.supply_arrivals) + [delayed_arrival]}
    )
    delayed_risks = {
        (r.depot_id, r.fuel_type): r
        for r in calculate_depot_risks(snap_delayed, horizon_hours=24.0)
    }
    target_delayed = delayed_risks[(depot_id, fuel.value)]

    # Arrival is outside 24h window, so scheduled_arrivals drops back to baseline
    assert target_delayed.scheduled_arrivals == base_target.scheduled_arrivals
    assert target_delayed.net_cover_liters == base_target.net_cover_liters
    assert target_delayed.net_cover_liters < target_with_arr.net_cover_liters


def test_supply_shortfall_halves_arrival_quantity():
    """Supply shortfall factor (0.5) halves arrival volume and drops net cover."""
    snapshot = base_snapshot()
    depot_id = snapshot.depots[0].id
    fuel = FuelType.DIESEL

    full_arrival = SupplyArrival(
        id="arr-test-2",
        depot_id=depot_id,
        fuel_type=fuel,
        quantity=10000.0,
        planned_tick=20,
        actual_tick=None,
        status=SupplyArrivalStatus.SCHEDULED,
    )
    snap_full = snapshot.model_copy(
        update={"supply_arrivals": list(snapshot.supply_arrivals) + [full_arrival]}
    )
    risks_full = {
        (r.depot_id, r.fuel_type): r for r in calculate_depot_risks(snap_full, horizon_hours=24.0)
    }

    shortfall_arrival = full_arrival.model_copy(update={"quantity": 5000.0})
    snap_shortfall = snapshot.model_copy(
        update={"supply_arrivals": list(snapshot.supply_arrivals) + [shortfall_arrival]}
    )
    risks_shortfall = {
        (r.depot_id, r.fuel_type): r
        for r in calculate_depot_risks(snap_shortfall, horizon_hours=24.0)
    }

    rf = risks_full[(depot_id, fuel.value)]
    rs = risks_shortfall[(depot_id, fuel.value)]

    assert rf.scheduled_arrivals - rs.scheduled_arrivals == 5000.0
    assert rf.net_cover_liters - rs.net_cover_liters == 5000.0


def test_unrelated_depot_unaffected():
    """Altering arrivals or stock at depot A does not affect depot B's cover curve."""
    snapshot = base_snapshot()
    assert len(snapshot.depots) >= 2
    depot_a = snapshot.depots[0].id
    depot_b = snapshot.depots[1].id
    fuel = FuelType.DIESEL

    base_risks = {
        (r.depot_id, r.fuel_type): r for r in calculate_depot_risks(snapshot, horizon_hours=24.0)
    }
    b_before = base_risks[(depot_b, fuel.value)]

    # Modify depot A with a large arrival
    arrival_a = SupplyArrival(
        id="arr-a",
        depot_id=depot_a,
        fuel_type=fuel,
        quantity=20000.0,
        planned_tick=10,
        actual_tick=None,
        status=SupplyArrivalStatus.SCHEDULED,
    )
    snap_mod = snapshot.model_copy(
        update={"supply_arrivals": list(snapshot.supply_arrivals) + [arrival_a]}
    )
    mod_risks = {
        (r.depot_id, r.fuel_type): r for r in calculate_depot_risks(snap_mod, horizon_hours=24.0)
    }
    b_after = mod_risks[(depot_b, fuel.value)]

    assert b_before.current_inventory == b_after.current_inventory
    assert b_before.scheduled_arrivals == b_after.scheduled_arrivals
    assert b_before.projected_demand == b_after.projected_demand
    assert b_before.net_cover_liters == b_after.net_cover_liters
    assert b_before.cover_hours == b_after.cover_hours
