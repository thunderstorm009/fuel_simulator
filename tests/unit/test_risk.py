import time

from core.forecast import KnownArrival
from core.risk import classify, confidence, monte_carlo


def test_monte_carlo_is_deterministic_and_returns_ordered_uncertainty_bands() -> None:
    kwargs = {
        "inventory": 100,
        "expected_rates": [10.0] * 96,
        "noise": 0.10,
        "tick_minutes": 15,
        "seed": 42,
    }

    first = monte_carlo(**kwargs)
    second = monte_carlo(**kwargs)

    assert first == second
    assert first.stockout_probability_24h == 1.0
    assert first.p10_hours <= first.p50_hours <= first.p90_hours
    assert first.trajectory[0].p10_inventory == 100


def test_more_demand_never_reduces_stockout_probability() -> None:
    baseline = monte_carlo(1000, [10.0] * 96, noise=0.1, tick_minutes=15, seed=7)
    increased = monte_carlo(1000, [20.0] * 96, noise=0.1, tick_minutes=15, seed=7)

    assert increased.stockout_probability_24h >= baseline.stockout_probability_24h
    assert increased.p50_hours <= baseline.p50_hours


def test_more_arrivals_never_increase_stockout_probability_or_advance_quantile() -> None:
    baseline = monte_carlo(100, [10.0] * 96, noise=0, tick_minutes=15, seed=3)
    with_arrival = monte_carlo(
        100,
        [10.0] * 96,
        noise=0,
        tick_minutes=15,
        seed=3,
        arrivals=[KnownArrival(tick=5, quantity=100)],
    )

    assert with_arrival.stockout_probability_24h <= baseline.stockout_probability_24h
    assert with_arrival.p50_hours >= baseline.p50_hours


def test_risk_classification_and_confidence_boundaries() -> None:
    assert classify(5.9, 1.0) == "critical"
    assert classify(6, 1.0) == "high"
    assert classify(12, 1.0) == "medium"
    assert classify(24, 1.0) == "ok"
    assert classify(None, 0.0) == "ok"
    assert confidence("HEALTHY", 6, 1.0) == 1.0
    assert confidence("DEGRADED", 6, 1.0) < confidence("HEALTHY", 6, 1.0)
    assert confidence("HEALTHY", 2, 1.0) < 0.5


def test_all_twelve_pairs_complete_under_fifty_milliseconds() -> None:
    started = time.perf_counter()
    for _ in range(12):
        monte_carlo(10000, [100.0] * 96, noise=0.1, tick_minutes=15, seed=19)
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert elapsed_ms < 50
