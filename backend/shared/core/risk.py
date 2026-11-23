"""Vectorized, seeded Monte Carlo stockout-risk estimates."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import pstdev

import numpy as np

from core.forecast import (
    KnownArrival,
    calibrate_ratio,
    expected_demand,
    future_demand_rates,
    hours_to_stockout,
    project_inventory,
    station_allocation_arrivals,
)
from core.models import Forecast, FuelType, RiskLevel, SimEvent, SimEventType, Snapshot, Station
from core.version import MODEL_VERSION
from core.world import PROFILE_NOISE


@dataclass(frozen=True)
class TrajectoryPoint:
    tick_offset: int
    mean_inventory: float
    p10_inventory: float
    p90_inventory: float


@dataclass(frozen=True)
class MonteCarloResult:
    stockout_probability_24h: float
    p10_hours: float
    p50_hours: float
    p90_hours: float
    trajectory: list[TrajectoryPoint]


@dataclass(frozen=True)
class ForecastRecord:
    forecast: Forecast
    trajectory: list[TrajectoryPoint]
    drivers: dict[str, object]
    source: str = "local"


def monte_carlo(
    inventory: float,
    expected_rates: Sequence[float],
    *,
    noise: float,
    tick_minutes: int,
    arrivals: Sequence[KnownArrival] = (),
    current_tick: int = 0,
    n: int = 300,
    seed: int | None = None,
) -> MonteCarloResult:
    if not expected_rates:
        raise ValueError("expected_rates must contain at least one tick")
    if tick_minutes <= 0 or n <= 0:
        raise ValueError("tick_minutes and n must be positive")
    if noise < 0:
        raise ValueError("noise must be non-negative")

    horizon = len(expected_rates)
    rates = np.asarray(expected_rates, dtype=np.float64)
    rng = np.random.default_rng(seed)
    profile_noise = np.maximum(0.0, 1 + rng.normal(0, noise, size=(n, horizon)))
    rate_uncertainty = np.maximum(0.0, 1 + rng.normal(0, 0.10, size=(n, horizon)))
    demand = rates[None, :] * profile_noise * rate_uncertainty

    arrival_by_offset: dict[int, float] = {}
    for arrival in arrivals:
        offset = arrival.tick - current_tick
        if 1 <= offset <= horizon and arrival.quantity > 0:
            arrival_by_offset[offset] = arrival_by_offset.get(offset, 0.0) + arrival.quantity

    levels = np.zeros((n, horizon + 1), dtype=np.float64)
    levels[:, 0] = max(0.0, inventory)
    for offset in range(1, horizon + 1):
        inbound = arrival_by_offset.get(offset, 0.0)
        levels[:, offset] = np.maximum(0.0, levels[:, offset - 1] + inbound - demand[:, offset - 1])

    stockouts = levels[:, 1:] <= 0
    has_stockout = stockouts.any(axis=1)
    first_offsets = np.argmax(stockouts, axis=1) + 1
    hours = np.where(has_stockout, first_offsets * tick_minutes / 60, 24.0)
    stockout_probability = float(np.mean(has_stockout))
    if inventory <= 0:
        stockout_probability = 1.0
        hours = np.zeros(n, dtype=np.float64)
    mean_levels = np.mean(levels, axis=0)
    p10_levels = np.quantile(levels, 0.10, axis=0)
    p90_levels = np.quantile(levels, 0.90, axis=0)
    points = [
        TrajectoryPoint(
            tick_offset=offset,
            mean_inventory=float(mean_levels[offset]),
            p10_inventory=float(p10_levels[offset]),
            p90_inventory=float(p90_levels[offset]),
        )
        for offset in range(horizon + 1)
    ]
    return MonteCarloResult(
        stockout_probability_24h=stockout_probability,
        p10_hours=float(np.quantile(hours, 0.10)),
        p50_hours=float(np.quantile(hours, 0.50)),
        p90_hours=float(np.quantile(hours, 0.90)),
        trajectory=points,
    )


def classify(hours_to_stockout: float | None, probability: float) -> str:
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1")
    if probability == 0:
        return "ok"
    if hours_to_stockout is None:
        return "medium" if probability >= 0.1 else "ok"
    if hours_to_stockout < 6:
        return "critical"
    if hours_to_stockout < 12:
        return "high"
    if hours_to_stockout < 24:
        return "medium"
    return "ok"


def confidence(data_status: str, history_len: int, ratio_stability: float) -> float:
    status = getattr(data_status, "value", data_status)
    status_factor = {"HEALTHY": 1.0, "DEGRADED": 0.5, "OFFLINE": 0.2}.get(status, 0.2)
    history_factor = min(1.0, max(0, history_len) / 6)
    stability_factor = min(1.0, max(0.0, ratio_stability))
    return status_factor * history_factor * stability_factor


def get_station_multiplier_at_tick(
    events: Sequence[SimEvent],
    station_id: str,
    tick: int,
    fallback: float = 1.0,
) -> float:
    """Return active demand multiplier if a DEMAND_SPIKE event targets this station."""
    for event in events:
        if event.type is SimEventType.DEMAND_SPIKE and event.start_tick <= tick <= event.end_tick:
            target = event.parameters.get("station_id")
            if target in (None, station_id):
                return float(event.parameters.get("multiplier", fallback))
    return fallback


def forecast_pair(
    snapshot: Snapshot,
    station: Station,
    fuel: str | FuelType,
    *,
    seed: int | None = None,
) -> ForecastRecord:
    fuel_type = FuelType(getattr(fuel, "value", fuel))
    tick_minutes = snapshot.instance.tick_minutes
    history = sorted(
        (
            row
            for row in snapshot.demand_history
            if row.station_id == station.id and row.fuel_type is fuel_type
        ),
        key=lambda row: (row.tick, row.id),
    )[-100:]
    expected_history = [
        expected_demand(
            station.demand_profile,
            fuel_type,
            row.sim_time,
            (
                getattr(row, "multiplier", None)
                or (
                    get_station_multiplier_at_tick(snapshot.events, station.id, row.tick, 1.0)
                    if MODEL_VERSION >= "1.2.0"
                    else 1.0
                )
            ),
            tick_minutes,
        )
        for row in history
    ]
    observed_history = [row.demand_liters for row in history]
    ratio = calibrate_ratio(observed_history, expected_history)
    sample_ratios = [
        observed / expected
        for observed, expected in zip(observed_history, expected_history)
        if expected > 0
    ]
    ratio_stability = max(0.0, 1.0 - pstdev(sample_ratios)) if len(sample_ratios) > 1 else 1.0
    data_status = snapshot.data_status.value
    if snapshot.stale and data_status == "HEALTHY":
        data_status = "DEGRADED"
    score = confidence(data_status, len(history), ratio_stability)
    rates = future_demand_rates(
        station.demand_profile,
        fuel_type,
        snapshot.instance.sim_time,
        station.demand_multiplier,
        ratio,
        tick_minutes,
    )
    arrivals = station_allocation_arrivals(snapshot, station.id, fuel_type)
    deterministic = project_inventory(
        station.inventory[fuel_type], rates, arrivals, start_tick=snapshot.instance.tick
    )
    hours = hours_to_stockout(
        deterministic.stockout_tick,
        current_tick=snapshot.instance.tick,
        tick_minutes=tick_minutes,
    )
    uncertainty = monte_carlo(
        station.inventory[fuel_type],
        rates,
        noise=PROFILE_NOISE[station.demand_profile],
        tick_minutes=tick_minutes,
        arrivals=arrivals,
        current_tick=snapshot.instance.tick,
        seed=seed,
    )
    risk = classify(hours, uncertainty.stockout_probability_24h)
    forecast = Forecast(
        station_id=station.id,
        fuel_type=fuel_type,
        hours_to_stockout=hours,
        p10_hours=uncertainty.p10_hours,
        p50_hours=uncertainty.p50_hours,
        p90_hours=uncertainty.p90_hours,
        stockout_probability_24h=uncertainty.stockout_probability_24h,
        confidence=score,
        risk_level=RiskLevel(risk),
        needs_review=score < 0.5,
    )
    return ForecastRecord(
        forecast=forecast,
        trajectory=uncertainty.trajectory,
        drivers={
            "demand_multiplier": station.demand_multiplier,
            "recent_ratio": ratio,
            "history_ticks": len(history),
            "arrivals": [
                {"tick": arrival.tick, "quantity": arrival.quantity} for arrival in arrivals
            ],
        },
    )
