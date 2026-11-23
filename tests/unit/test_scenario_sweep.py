"""Unit tests for scenario sweep generation, statistics, win/loss tracking, and bootstrap CI."""

from core.scenario_sweep import (
    compute_bootstrap_ci,
    compute_sweep_statistics,
    compute_win_tie_loss,
    find_losses,
    generate_crisis_scenarios,
)


def test_generate_crisis_scenarios_reproducibility():
    s1 = generate_crisis_scenarios(seed=42, count=60, holdout_count=10)
    s2 = generate_crisis_scenarios(seed=42, count=60, holdout_count=10)
    assert len(s1) == 60
    assert len(s2) == 60
    assert [s.id for s in s1] == [s.id for s in s2]
    assert s1[0].events == s2[0].events
    assert s1[-1].events == s2[-1].events


def test_generate_crisis_scenarios_holdout_segregation():
    scenarios = generate_crisis_scenarios(seed=42, count=60, holdout_count=10)
    training = [s for s in scenarios if not s.is_holdout]
    holdout = [s for s in scenarios if s.is_holdout]
    assert len(training) == 50
    assert len(holdout) == 10
    # Holdout scenarios should have distinct IDs
    assert all("holdout" in s.id for s in holdout)
    assert all("holdout" not in s.id for s in training)


def test_compute_sweep_statistics():
    data = [0.90, 0.95, 0.98, 1.0, 1.0, 0.85, 0.92, 0.99, 1.0, 0.80]
    stats = compute_sweep_statistics(data)
    assert abs(stats["mean"] - 0.939) < 0.001
    assert abs(stats["median"] - 0.965) < 0.001
    assert stats["min"] == 0.80
    assert stats["max"] == 1.0
    assert 0.80 <= stats["p10"] <= 0.90


def test_compute_win_tie_loss():
    a = [1.0, 0.95, 0.90, 0.85, 1.0]
    b = [1.0, 0.90, 0.95, 0.80, 1.0]
    # pairs:
    # 1.0 vs 1.0 -> tie
    # 0.95 vs 0.90 -> win for a
    # 0.90 vs 0.95 -> loss for a
    # 0.85 vs 0.80 -> win for a
    # 1.0 vs 1.0 -> tie
    res = compute_win_tie_loss(a, b, epsilon=1e-3)
    assert res["wins"] == 2
    assert res["ties"] == 2
    assert res["losses"] == 1


def test_compute_bootstrap_ci():
    a = [0.98, 0.99, 1.0, 0.97, 0.95, 0.96, 1.0, 0.98, 0.99, 0.97]
    b = [0.85, 0.88, 0.90, 0.82, 0.80, 0.84, 0.89, 0.85, 0.87, 0.83]
    mean_diff, lower, upper = compute_bootstrap_ci(a, b, num_resamples=500, seed=42)
    assert mean_diff > 0.10
    assert lower > 0.08
    assert upper > lower
    assert lower <= mean_diff <= upper


def test_find_losses():
    scenario_results = [
        {
            "scenario_id": "sc_01",
            "scenario_name": "Mild Surge",
            "heuristic_svc": 1.0,
            "naive_svc": 0.95,
        },
        {
            "scenario_id": "sc_02",
            "scenario_name": "Route Closure After Refill",
            "heuristic_svc": 0.92,
            "naive_svc": 0.96,
            "heuristic_unmet": 1500.0,
            "naive_unmet": 800.0,
        },
    ]
    losses = find_losses(
        scenario_results,
        primary_key="heuristic_svc",
        baseline_key="naive_svc",
        epsilon=1e-3,
    )
    assert len(losses) == 1
    assert losses[0]["scenario_id"] == "sc_02"
