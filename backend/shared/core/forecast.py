"""Pure demand calibration and on-hand inventory projection functions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil

from core.models import AllocationStatus, FuelType, Snapshot
from core.world import DAILY_LITERS, hour_factor


@dataclass(frozen=True)
class KnownArrival:
    tick: int
    quantity: float


@dataclass(frozen=True)
class Projection:
    trajectory: list[float]
    stockout_tick: int | None


def expected_demand(
    profile: str,
    fuel: str,
    sim_time: datetime,
    multiplier: float,
    tick_minutes: int,
) -> float:
    if tick_minutes <= 0 or tick_minutes > 1440:
        raise ValueError("tick_minutes must be between 1 and 1440")
    fuel_name = getattr(fuel, "value", fuel).upper()
    try:
        daily_liters = DAILY_LITERS[profile][fuel_name]
    except KeyError as exc:
        raise ValueError(f"unknown profile/fuel pair: {profile}/{fuel}") from exc
    return (
        daily_liters / (1440 / tick_minutes) * hour_factor(profile, sim_time) * max(0.0, multiplier)
    )


def calibrate_ratio(
    observed: Sequence[float],
    expected: Sequence[float],
    alpha: float = 0.3,
    lower: float = 0.5,
    upper: float = 2.0,
) -> float:
    if len(observed) != len(expected):
        raise ValueError("observed and expected must have the same length")
    if not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")
    if lower <= 0 or upper < lower:
        raise ValueError("invalid calibration clamp")
    ratio = 1.0
    for actual, baseline in zip(observed, expected):
        if baseline <= 0:
            continue
        sample_ratio = actual / baseline
        ratio = alpha * sample_ratio + (1 - alpha) * ratio
        ratio = min(upper, max(lower, ratio))
    return ratio


def project_inventory(
    inventory: float,
    rates: Sequence[float],
    arrivals: Sequence[KnownArrival],
    *,
    start_tick: int = 0,
) -> Projection:
    arrivals_by_tick: dict[int, float] = {}
    for arrival in arrivals:
        if arrival.quantity > 0:
            arrivals_by_tick[arrival.tick] = (
                arrivals_by_tick.get(arrival.tick, 0.0) + arrival.quantity
            )

    level = max(0.0, inventory)
    trajectory = [level]
    stockout_tick = start_tick if level <= 0 else None
    for offset, rate in enumerate(rates, start=1):
        tick = start_tick + offset
        level = max(0.0, level + arrivals_by_tick.get(tick, 0.0) - max(0.0, rate))
        trajectory.append(level)
        if level <= 0 and stockout_tick is None:
            stockout_tick = tick
    return Projection(trajectory=trajectory, stockout_tick=stockout_tick)


def hours_to_stockout(
    stockout_tick: int | None,
    *,
    current_tick: int,
    tick_minutes: int,
) -> float | None:
    if tick_minutes <= 0:
        raise ValueError("tick_minutes must be positive")
    if stockout_tick is None:
        return None
    return max(0, stockout_tick - current_tick) * tick_minutes / 60


def station_allocation_arrivals(
    snapshot: Snapshot, station_id: str, fuel: str | FuelType
) -> list[KnownArrival]:
    fuel_name = getattr(fuel, "value", fuel)
    route_durations = {route.id: route.transit_ticks for route in snapshot.routes}
    current_tick = snapshot.instance.tick
    arrivals: list[KnownArrival] = []
    for allocation in snapshot.allocations:
        if (
            allocation.destination_station_id != station_id
            or allocation.fuel_type.value != fuel_name
        ):
            continue
        if allocation.status is AllocationStatus.IN_TRANSIT:
            if allocation.expected_arrival_tick is not None:
                arrivals.append(KnownArrival(allocation.expected_arrival_tick, allocation.quantity))
        elif allocation.status is AllocationStatus.PENDING:
            transit = route_durations.get(allocation.route_id)
            if transit is not None:
                arrivals.append(KnownArrival(current_tick + 1 + transit, allocation.quantity))
    return sorted(arrivals, key=lambda arrival: arrival.tick)


def future_demand_rates(
    profile: str,
    fuel: str | FuelType,
    sim_time: datetime,
    multiplier: float,
    ratio: float,
    tick_minutes: int,
) -> list[float]:
    if tick_minutes <= 0:
        raise ValueError("tick_minutes must be positive")
    ticks = ceil(1440 / tick_minutes)
    return [
        expected_demand(
            profile,
            getattr(fuel, "value", fuel),
            sim_time + timedelta(minutes=tick_minutes * offset),
            multiplier * ratio,
            tick_minutes,
        )
        for offset in range(1, ticks + 1)
    ]
