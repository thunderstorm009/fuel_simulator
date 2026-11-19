from datetime import datetime, timedelta

import pytest

from core.forecast import (
    KnownArrival,
    calibrate_ratio,
    expected_demand,
    hours_to_stockout,
    project_inventory,
    station_allocation_arrivals,
)
from core.models import Allocation, FuelType, Snapshot, SupplyArrivalStatus
from core.risk import forecast_pair

SAMPLES = __import__("pathlib").Path(__file__).parents[2] / "docs" / "sim-samples"


def test_expected_demand_uses_tick_length_hour_factor_and_station_multiplier() -> None:
    # 8,500 / 96 ticks per day * 1.45 at 08:00 * 1.2 station multiplier.
    expected = (8500 / 96) * 1.45 * 1.2

    actual = expected_demand("urban_high", "DIESEL", datetime(2026, 1, 1, 8), 1.2, 15)

    assert actual == pytest.approx(expected)


def test_profile_hour_boundaries_are_inclusive() -> None:
    # Industrial 17:00 is the final high hour (1.55); 18:00 is low (0.45).
    at_boundary = expected_demand("industrial", "DIESEL", datetime(2026, 1, 1, 17), 1, 15)
    after_boundary = expected_demand("industrial", "DIESEL", datetime(2026, 1, 1, 18), 1, 15)

    assert at_boundary / after_boundary == pytest.approx(1.55 / 0.45)


def test_calibration_uses_clamped_ewma_of_observed_to_expected() -> None:
    # Start at 1.0: 1.0 -> (0.3*2 + 0.7*1)=1.3 -> (0.3*1 + 0.7*1.3)=1.21.
    ratio = calibrate_ratio([200, 100], [100, 100])
    clamped = calibrate_ratio([1000], [100])

    assert ratio == pytest.approx(1.21)
    assert clamped == 2.0


def test_projection_adds_arrival_before_demand_and_returns_first_stockout_tick() -> None:
    # Tick 1: 20 - 8 = 12; tick 2: 12 + 10 - 15 = 7; tick 3: 7 - 8 <= 0.
    projection = project_inventory(
        inventory=20,
        rates=[8, 15, 8],
        arrivals=[KnownArrival(tick=2, quantity=10)],
        start_tick=0,
    )

    assert projection.trajectory == pytest.approx([20, 12, 7, 0])
    assert projection.stockout_tick == 3
    assert hours_to_stockout(projection.stockout_tick, current_tick=0, tick_minutes=15) == 0.75


def test_more_demand_never_delays_stockout_and_more_arrivals_never_advance_it() -> None:
    baseline = project_inventory(100, [10] * 12, [], start_tick=0)
    more_demand = project_inventory(100, [12] * 12, [], start_tick=0)
    more_arrivals = project_inventory(
        100, [10] * 12, [KnownArrival(tick=4, quantity=60)], start_tick=0
    )

    assert more_demand.stockout_tick <= baseline.stockout_tick
    assert (
        more_arrivals.stockout_tick is None or more_arrivals.stockout_tick >= baseline.stockout_tick
    )


def test_zero_demand_has_no_stockout_and_stockout_time_handles_none() -> None:
    projection = project_inventory(100, [0] * 96, [], start_tick=20)

    assert projection.stockout_tick is None
    assert hours_to_stockout(None, current_tick=20, tick_minutes=15) is None


def test_invalid_tick_length_and_calibration_shapes_are_rejected() -> None:
    with pytest.raises(ValueError, match="tick_minutes"):
        expected_demand("urban_high", "DIESEL", datetime(2026, 1, 1), 1, 0)
    with pytest.raises(ValueError, match="same length"):
        calibrate_ratio([1], [1, 2])


def test_pending_and_in_transit_allocations_become_station_arrivals() -> None:
    snapshot = Snapshot.model_validate(
        {
            "instance": {**__import__("json").loads((SAMPLES / "instance.json").read_text())},
            "regions": __import__("json").loads((SAMPLES / "regions.json").read_text()),
            "depots": __import__("json").loads((SAMPLES / "depots.json").read_text()),
            "stations": __import__("json").loads((SAMPLES / "stations.json").read_text()),
            "routes": __import__("json").loads((SAMPLES / "routes.json").read_text()),
            "supply_arrivals": __import__("json").loads(
                (SAMPLES / "supply-arrivals.json").read_text()
            ),
            "events": __import__("json").loads((SAMPLES / "events.json").read_text()),
            "allocations": [],
            "demand_history": [],
            "metrics": __import__("json").loads((SAMPLES / "metrics.json").read_text()),
            "fetched_at": "2026-01-01T00:00:00Z",
            "stale": False,
            "data_status": "HEALTHY",
        }
    )
    snapshot.allocations = [
        Allocation.model_validate(
            {
                "id": 1,
                "idempotency_key": "transit",
                "source_depot_id": "depot-gazipur",
                "destination_station_id": "station-mirpur",
                "route_id": "route-gazipur-mirpur",
                "fuel_type": "DIESEL",
                "quantity": 500,
                "created_tick": 0,
                "departure_tick": 1,
                "expected_arrival_tick": 4,
                "actual_arrival_tick": None,
                "status": "IN_TRANSIT",
                "failure_reason": None,
            }
        ),
        Allocation.model_validate(
            {
                "id": 2,
                "idempotency_key": "pending",
                "source_depot_id": "depot-gazipur",
                "destination_station_id": "station-mirpur",
                "route_id": "route-gazipur-mirpur",
                "fuel_type": "DIESEL",
                "quantity": 200,
                "created_tick": 0,
                "departure_tick": None,
                "expected_arrival_tick": None,
                "actual_arrival_tick": None,
                "status": "PENDING",
                "failure_reason": None,
            }
        ),
    ]

    arrivals = station_allocation_arrivals(snapshot, "station-mirpur", "DIESEL")

    assert arrivals == [KnownArrival(tick=3, quantity=200), KnownArrival(tick=4, quantity=500)]


def _snapshot_with_history() -> Snapshot:
    import json

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
    raw["demand_history"] = json.loads((SAMPLES / "demand-history-96-ticks.json").read_text())
    raw["allocations"] = []
    raw["fetched_at"] = "2026-01-02T00:00:00Z"
    raw["stale"] = False
    raw["data_status"] = "HEALTHY"
    return Snapshot.model_validate(raw)


def test_demand_spike_clears_demand_multiplier_but_keeps_inventory_depletion() -> None:
    snapshot = _snapshot_with_history()
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    station.inventory[FuelType.DIESEL] = 3000

    baseline = forecast_pair(snapshot, station, "DIESEL", seed=42)
    spike_snapshot = snapshot.model_copy(deep=True)
    spike_station = next(row for row in spike_snapshot.stations if row.id == "station-mirpur")
    spike_station.demand_multiplier = 1.8
    spike = forecast_pair(spike_snapshot, spike_station, "DIESEL", seed=42)

    assert spike.drivers["demand_multiplier"] == 1.8
    assert spike.trajectory[1].mean_inventory < baseline.trajectory[1].mean_inventory
    assert spike.forecast.hours_to_stockout < baseline.forecast.hours_to_stockout

    event_ticks = 4
    tick_minutes = snapshot.instance.tick_minutes
    consumed = sum(
        expected_demand(
            station.demand_profile,
            "DIESEL",
            snapshot.instance.sim_time + timedelta(minutes=tick_minutes * offset),
            1.8,
            tick_minutes,
        )
        for offset in range(1, event_ticks + 1)
    )
    resolved_snapshot = snapshot.model_copy(deep=True)
    resolved_snapshot.instance.sim_time += timedelta(minutes=tick_minutes * event_ticks)
    resolved_snapshot.instance.tick += event_ticks
    resolved_station = next(row for row in resolved_snapshot.stations if row.id == "station-mirpur")
    resolved_station.inventory[FuelType.DIESEL] = 3000 - consumed
    resolved = forecast_pair(resolved_snapshot, resolved_station, "DIESEL", seed=42)

    normal_same_time_snapshot = snapshot.model_copy(deep=True)
    normal_same_time_snapshot.instance.sim_time = resolved_snapshot.instance.sim_time
    normal_same_time_snapshot.instance.tick = resolved_snapshot.instance.tick
    normal_same_time_station = next(
        row for row in normal_same_time_snapshot.stations if row.id == "station-mirpur"
    )
    normal_same_time_station.inventory[FuelType.DIESEL] = 3000
    normal_same_time = forecast_pair(
        normal_same_time_snapshot, normal_same_time_station, "DIESEL", seed=42
    )

    assert resolved.drivers["demand_multiplier"] == 1.0
    assert resolved.trajectory[0].mean_inventory == pytest.approx(3000 - consumed)
    resolved_first_tick_change = (
        resolved.trajectory[1].mean_inventory - resolved.trajectory[0].mean_inventory
    )
    normal_first_tick_change = (
        normal_same_time.trajectory[1].mean_inventory
        - normal_same_time.trajectory[0].mean_inventory
    )
    assert resolved_first_tick_change == pytest.approx(normal_first_tick_change)
    assert resolved.trajectory[0].mean_inventory < normal_same_time.trajectory[0].mean_inventory
    assert resolved.forecast.hours_to_stockout < normal_same_time.forecast.hours_to_stockout


def test_event_demand_forecast_moves_toward_baseline_after_multiplier_is_removed() -> None:
    snapshot = _snapshot_with_history()
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    tick_minutes = snapshot.instance.tick_minutes
    history = [
        row
        for row in snapshot.demand_history
        if row.station_id == station.id and row.fuel_type is FuelType.DIESEL
    ]
    observed = [row.demand_liters for row in history]
    expected = [
        expected_demand(station.demand_profile, FuelType.DIESEL, row.sim_time, 1.0, tick_minutes)
        for row in history
    ]
    baseline_ratio = calibrate_ratio(observed, expected)
    event_expected = [
        expected_demand(
            station.demand_profile,
            FuelType.DIESEL,
            snapshot.instance.sim_time + timedelta(minutes=tick_minutes * offset),
            1.0,
            tick_minutes,
        )
        for offset in range(1, 5)
    ]
    during_ratio = calibrate_ratio(
        observed + [rate * 1.8 for rate in event_expected], expected + event_expected
    )
    after_resolution_ratio = calibrate_ratio(
        observed + [rate * 1.8 for rate in event_expected] + event_expected,
        expected + event_expected + event_expected,
    )
    normal_rate = (
        expected_demand(
            station.demand_profile,
            FuelType.DIESEL,
            snapshot.instance.sim_time + timedelta(minutes=tick_minutes * 5),
            1.0,
            tick_minutes,
        )
        * baseline_ratio
    )
    during_event_rate = (
        expected_demand(
            station.demand_profile,
            FuelType.DIESEL,
            snapshot.instance.sim_time + timedelta(minutes=tick_minutes * 5),
            1.8,
            tick_minutes,
        )
        * during_ratio
    )
    after_resolution_rate = (
        expected_demand(
            station.demand_profile,
            FuelType.DIESEL,
            snapshot.instance.sim_time + timedelta(minutes=tick_minutes * 5),
            1.0,
            tick_minutes,
        )
        * after_resolution_ratio
    )

    assert during_event_rate > normal_rate
    assert normal_rate < after_resolution_rate < during_event_rate
    assert abs(after_resolution_rate - normal_rate) < abs(during_event_rate - normal_rate)


def test_unrelated_depot_shipment_delay_does_not_change_station_risk() -> None:
    snapshot = _snapshot_with_history()
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    assert snapshot.allocations == []
    baseline = forecast_pair(snapshot, station, "DIESEL", seed=42)
    baseline_shipment = next(row for row in snapshot.supply_arrivals if row.id == "supply-201")

    delayed_snapshot = snapshot.model_copy(deep=True)
    shipment = next(row for row in delayed_snapshot.supply_arrivals if row.id == "supply-201")
    shipment.planned_tick += 5
    shipment.status = SupplyArrivalStatus.DELAYED
    delayed_station = next(row for row in delayed_snapshot.stations if row.id == "station-mirpur")
    delayed = forecast_pair(delayed_snapshot, delayed_station, "DIESEL", seed=42)

    assert baseline_shipment.planned_tick == 128
    assert shipment.planned_tick == 133
    assert baseline.drivers["arrivals"] == []
    assert delayed == baseline
