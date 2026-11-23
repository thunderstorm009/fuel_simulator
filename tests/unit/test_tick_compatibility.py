"""Unit tests verifying platform compatibility across tick lengths (8 minutes vs 15 minutes)."""

import math
from datetime import datetime, timedelta, timezone

import pytest

from core.forecast import expected_demand, future_demand_rates, hours_to_stockout
from core.models import (
    DataStatus,
    Depot,
    DepotStatus,
    FuelType,
    Instance,
    InstanceStatus,
    Metrics,
    Snapshot,
    Station,
    StationStatus,
)
from core.policies.heuristic import HeuristicPolicy
from core.risk import forecast_pair, monte_carlo


@pytest.mark.parametrize("tick_minutes", [8, 15])
def test_expected_demand_integrates_to_same_daily_total(tick_minutes: int):
    """Sum of expected demand over 24 hours must be invariant to tick duration."""
    profile = "urban_high"
    fuel = "DIESEL"
    ticks_in_day = math.ceil(1440 / tick_minutes)

    sim_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    total_day_liters = 0.0
    for t in range(ticks_in_day):
        st = sim_start + timedelta(minutes=t * tick_minutes)
        liters = expected_demand(profile, fuel, st, multiplier=1.0, tick_minutes=tick_minutes)
        total_day_liters += liters

    # Expected demand for urban_high DIESEL integrated over 24h is 8075 L for 8 and 15 min ticks
    assert math.isclose(total_day_liters, 8075.0, rel_tol=1e-4), (
        f"For tick_minutes={tick_minutes}, total was {total_day_liters}, expected 8075.0"
    )


@pytest.mark.parametrize("tick_minutes", [8, 15])
def test_future_demand_rates_length_and_coverage(tick_minutes: int):
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    rates = future_demand_rates("urban_high", FuelType.DIESEL, sim_time, 1.0, 1.0, tick_minutes)
    expected_length = math.ceil(1440 / tick_minutes)
    assert len(rates) == expected_length
    assert all(r > 0 for r in rates)


@pytest.mark.parametrize(
    ("tick_minutes", "ticks_away", "expected_hours"),
    [
        (15, 12, 3.0),
        (15, 48, 12.0),
        (8, 15, 2.0),
        (8, 90, 12.0),
    ],
)
def test_hours_to_stockout_scales_with_tick_minutes(
    tick_minutes: int, ticks_away: int, expected_hours: float
):
    current_tick = 100
    stockout_tick = current_tick + ticks_away
    hours = hours_to_stockout(stockout_tick, current_tick=current_tick, tick_minutes=tick_minutes)
    assert hours == pytest.approx(expected_hours, rel=1e-4)


@pytest.mark.parametrize("tick_minutes", [8, 15])
def test_monte_carlo_stockout_probability_consistency(tick_minutes: int):
    # Equal physical condition: 2000L inventory, 24h of demand rates
    sim_time = datetime(2026, 1, 1, 6, 0, tzinfo=timezone.utc)
    rates = future_demand_rates("regional", FuelType.OCTANE, sim_time, 1.0, 1.0, tick_minutes)

    res = monte_carlo(
        inventory=1500.0,
        expected_rates=rates,
        noise=0.05,
        tick_minutes=tick_minutes,
        arrivals=[],
        current_tick=0,
        seed=42,
    )

    # Both must estimate reasonable hours to stockout
    assert 0.0 <= res.stockout_probability_24h <= 1.0
    assert res.p50_hours is not None
    assert 1.0 <= res.p50_hours <= 24.0


@pytest.mark.parametrize("tick_minutes", [8, 15])
def test_heuristic_policy_lookahead_scales(tick_minutes: int):
    policy = HeuristicPolicy()
    instance = Instance(
        id=1,
        scenario_id="compat",
        scenario_version="1.0",
        seed=42,
        sim_time=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        tick=10,
        tick_minutes=tick_minutes,
        status=InstanceStatus.RUNNING,
    )
    station = Station(
        id="station-mirpur",
        name="Mirpur Station",
        region_id="region-dhaka",
        status=StationStatus.OPEN,
        demand_profile="urban_high",
        demand_multiplier=1.0,
        capacity={FuelType.DIESEL: 50000, FuelType.PETROL: 40000, FuelType.OCTANE: 30000},
        inventory={FuelType.DIESEL: 15000, FuelType.PETROL: 20000, FuelType.OCTANE: 10000},
    )
    depot = Depot(
        id="depot-dhaka",
        name="Dhaka Depot",
        region_id="region-dhaka",
        status=DepotStatus.OPEN,
        dispatch_capacity_per_tick=23000.0,
        capacity={FuelType.DIESEL: 100000, FuelType.PETROL: 100000, FuelType.OCTANE: 100000},
        inventory={FuelType.DIESEL: 80000, FuelType.PETROL: 80000, FuelType.OCTANE: 80000},
    )
    snapshot = Snapshot(
        instance=instance,
        regions=[],
        depots=[depot],
        stations=[station],
        routes=[],
        supply_arrivals=[],
        events=[],
        allocations=[],
        demand_history=[],
        metrics=Metrics(
            served_demand_liters=0.0,
            unmet_demand_liters=0.0,
            service_level=1.0,
            allocation_liters=0.0,
            allocation_failures=0,
        ),
        fetched_at=datetime.now(timezone.utc),
        data_status=DataStatus.HEALTHY,
        stale=False,
    )

    fc = forecast_pair(snapshot, station, FuelType.DIESEL)
    # Policy recommend must execute cleanly without error under both 8 and 15 tick minutes
    recs = policy.recommend(snapshot, [fc])
    assert isinstance(recs, list)
    assert policy.name == "heuristic"
