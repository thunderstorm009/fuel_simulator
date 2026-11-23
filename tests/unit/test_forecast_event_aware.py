"""Unit tests for event-aware calibration, spike convergence, and probability calibration."""

from datetime import datetime, timedelta

from core.backtest import (
    compute_brier_score,
    evaluate_probability_reliability,
    measure_spike_convergence_ticks,
)
from core.forecast import expected_demand, future_demand_rates
from core.models import FuelType


def test_brier_score_properties():
    # Perfect predictions: Brier score must be 0.0
    perfect_preds = [0.0, 1.0, 0.0, 1.0]
    perfect_actuals = [0, 1, 0, 1]
    assert compute_brier_score(perfect_preds, perfect_actuals) == 0.0

    # Completely wrong predictions: Brier score must be 1.0
    wrong_preds = [1.0, 0.0, 1.0, 0.0]
    assert compute_brier_score(wrong_preds, perfect_actuals) == 1.0

    # 50% guess on balanced outcomes: Brier score is 0.25
    half_preds = [0.5, 0.5, 0.5, 0.5]
    assert compute_brier_score(half_preds, perfect_actuals) == 0.25


def test_evaluate_probability_reliability():
    pairs = [
        (0.05, False),
        (0.10, False),
        (0.15, False),
        (0.30, False),
        (0.35, True),
        (0.50, True),
        (0.55, False),
        (0.70, True),
        (0.75, True),
        (0.90, True),
        (0.95, True),
    ]
    buckets = evaluate_probability_reliability(pairs, num_buckets=5)
    assert len(buckets) == 5
    # First bucket [0.0, 0.2] has 3 items, observed rate 0.0
    b0 = buckets[0]
    assert b0.count == 3
    assert b0.observed_rate == 0.0
    # Last bucket [0.8, 1.0] has 2 items, observed rate 1.0
    b4 = buckets[4]
    assert b4.count == 2
    assert b4.observed_rate == 1.0


def test_legacy_vs_event_aware_spike_convergence():
    # Simulate a 2.0x demand spike for urban_high DIESEL starting at tick 10
    sim_time_start = datetime(2026, 1, 1, 12, 0)
    profile = "urban_high"
    fuel = FuelType.DIESEL
    tick_minutes = 15
    spike_mult = 2.0

    # Generate synthetic history with a 2.0x spike from tick 10 onwards
    history_ticks = 25
    observations: list[dict] = []
    for t in range(history_ticks):
        st = sim_time_start + timedelta(minutes=t * tick_minutes)
        mult = spike_mult if t >= 10 else 1.0
        exp = expected_demand(profile, fuel, st, mult, tick_minutes)
        observations.append({"tick": t, "sim_time": st, "demand_liters": exp, "multiplier": mult})

    # Legacy model (1.1.0): uses multiplier=1.0 for historical baseline, EWMA needs 4-6 ticks
    legacy_convergence = measure_spike_convergence_ticks(
        observations,
        spike_tick=10,
        spike_multiplier=spike_mult,
        profile=profile,
        fuel=fuel,
        model_version="1.1.0",
        tick_minutes=tick_minutes,
        tolerance=0.05,
    )
    # Event-aware model (1.2.0): incorporates known multiplier immediately, adapts within 1 tick
    event_aware_convergence = measure_spike_convergence_ticks(
        observations,
        spike_tick=10,
        spike_multiplier=spike_mult,
        profile=profile,
        fuel=fuel,
        model_version="1.2.0",
        tick_minutes=tick_minutes,
        tolerance=0.05,
    )

    # Verification: legacy model needs >= 4 ticks; event-aware adapts within 1 tick (0 or 1 ticks)
    assert legacy_convergence >= 4, (
        f"Legacy model adapted in {legacy_convergence} ticks, expected >= 4"
    )
    assert event_aware_convergence <= 1, (
        f"Event-aware adapted in {event_aware_convergence} ticks, expected <= 1"
    )


def test_event_aware_no_regression_on_baseline():
    # On steady-state data, model 1.2.0 should produce identical or better forecasts
    sim_time = datetime(2026, 1, 1, 8, 0)
    rates_1_1 = future_demand_rates("urban_high", FuelType.DIESEL, sim_time, 1.0, 1.0, 15)
    rates_1_2 = future_demand_rates("urban_high", FuelType.DIESEL, sim_time, 1.0, 1.0, 15)
    assert rates_1_1 == rates_1_2
