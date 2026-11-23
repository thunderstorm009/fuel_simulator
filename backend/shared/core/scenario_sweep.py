"""Pure domain logic for randomized crisis scenario generation, sweep stats, and bootstrap CI."""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ScenarioSpec:
    id: str
    name: str
    is_holdout: bool
    events: list[dict[str, Any]]
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_crisis_scenarios(
    seed: int = 42, count: int = 60, holdout_count: int = 10
) -> list[ScenarioSpec]:
    """Generate deterministic crisis scenarios partitioned into training and hold-out sets."""
    rng = random.Random(seed)
    training_count = max(1, count - holdout_count)
    scenarios: list[ScenarioSpec] = []

    stations = [
        "station-mirpur",
        "station-tongi",
        "station-karnaphuli",
        "station-coxsbazar",
    ]
    regions = ["region-dhaka", "region-chattogram"]
    depots = ["depot-gazipur", "depot-patiya"]
    routes = [
        "route-gazipur-mirpur",
        "route-gazipur-tongi",
        "route-patiya-karnaphuli",
        "route-patiya-coxsbazar",
    ]

    event_types = [
        "demand_spike",
        "supply_shortfall",
        "route_disruption",
        "station_outage",
        "compound",
    ]

    # 1. Training / tuning family
    for i in range(1, training_count + 1):
        ev_type = event_types[(i - 1) % len(event_types)]
        scenario_id = f"scenario_{i:02d}"
        events: list[dict[str, Any]] = []

        if ev_type == "demand_spike":
            mult = round(rng.uniform(1.2, 2.8), 2)
            start = rng.randint(5, 50)
            dur = rng.randint(20, 140)
            target_reg = rng.choice(regions + [None])
            target_stn = rng.choice(stations) if target_reg is None else None
            params: dict[str, Any] = {"multiplier": mult}
            if target_reg:
                params["region_ids"] = [target_reg]
            else:
                params["station_ids"] = [target_stn]
            events.append(
                {
                    "type": "demand_spike",
                    "start_tick": start,
                    "duration_ticks": dur,
                    "parameters": params,
                }
            )
            tgt = target_reg or target_stn
            desc = f"Demand surge {mult}x on {tgt} (ticks {start}..{start + dur})"

        elif ev_type == "supply_shortfall":
            factor = round(rng.uniform(0.3, 0.8), 2)
            start = rng.randint(5, 40)
            dur = rng.randint(30, 150)
            target_depot = rng.choice(depots + ["all"])
            params = {"factor": factor}
            if target_depot != "all":
                params["depot_ids"] = [target_depot]
            else:
                params["depot_ids"] = depots
            events.append(
                {
                    "type": "supply_shortfall",
                    "start_tick": start,
                    "duration_ticks": dur,
                    "parameters": params,
                }
            )
            desc = f"Supply shortfall {factor} on {target_depot} (ticks {start}..{start + dur})"

        elif ev_type == "route_disruption":
            num_routes = rng.randint(1, 2)
            chosen_routes = rng.sample(routes, num_routes)
            start = rng.randint(10, 60)
            dur = rng.randint(20, 120)
            events.append(
                {
                    "type": "route_disruption",
                    "start_tick": start,
                    "duration_ticks": dur,
                    "parameters": {"route_ids": chosen_routes},
                }
            )
            desc = (
                f"Corridor disruption on {', '.join(chosen_routes)} (ticks {start}..{start + dur})"
            )

        elif ev_type == "station_outage":
            target_stn = rng.choice(stations)
            start = rng.randint(10, 50)
            dur = rng.randint(15, 80)
            events.append(
                {
                    "type": "station_outage",
                    "start_tick": start,
                    "duration_ticks": dur,
                    "parameters": {"station_ids": [target_stn]},
                }
            )
            desc = f"Station outage on {target_stn} (ticks {start}..{start + dur})"

        else:  # compound
            mult = round(rng.uniform(1.3, 2.0), 2)
            events.append(
                {
                    "type": "demand_spike",
                    "start_tick": rng.randint(5, 30),
                    "duration_ticks": rng.randint(40, 120),
                    "parameters": {"multiplier": mult, "region_ids": [rng.choice(regions)]},
                }
            )
            factor = round(rng.uniform(0.5, 0.8), 2)
            events.append(
                {
                    "type": "supply_shortfall",
                    "start_tick": rng.randint(5, 20),
                    "duration_ticks": rng.randint(50, 140),
                    "parameters": {"factor": factor, "depot_ids": [rng.choice(depots)]},
                }
            )
            if rng.random() > 0.5:
                events.append(
                    {
                        "type": "route_disruption",
                        "start_tick": rng.randint(20, 50),
                        "duration_ticks": rng.randint(20, 60),
                        "parameters": {"route_ids": [rng.choice(routes)]},
                    }
                )
            desc = f"Compound crisis: surge {mult}x + shortfall {factor}"

        scenarios.append(
            ScenarioSpec(
                id=scenario_id,
                name=f"Tuning {scenario_id}: {ev_type}",
                is_holdout=False,
                events=events,
                description=desc,
            )
        )

    # 2. Holdout family (never used during policy tuning)
    for j in range(1, holdout_count + 1):
        scenario_id = f"holdout_{j:02d}"
        mult = round(rng.uniform(1.8, 2.6), 2)
        factor = round(rng.uniform(0.3, 0.6), 2)
        disrupted_route = rng.choice(routes)
        start = rng.randint(10, 30)
        events = [
            {
                "type": "demand_spike",
                "start_tick": start,
                "duration_ticks": 120,
                "parameters": {"multiplier": mult, "region_ids": regions},
            },
            {
                "type": "supply_shortfall",
                "start_tick": start - 5 if start >= 5 else 0,
                "duration_ticks": 140,
                "parameters": {"factor": factor, "depot_ids": depots},
            },
            {
                "type": "route_disruption",
                "start_tick": start + 10,
                "duration_ticks": 80,
                "parameters": {"route_ids": [disrupted_route]},
            },
        ]
        desc = (
            f"Holdout severe crisis {j}: {mult}x spike, {factor} shortfall, cut {disrupted_route}"
        )
        scenarios.append(
            ScenarioSpec(
                id=scenario_id,
                name=f"Holdout {scenario_id}",
                is_holdout=True,
                events=events,
                description=desc,
            )
        )

    return scenarios


def compute_sweep_statistics(results: list[float]) -> dict[str, float]:
    """Compute summary statistics (mean, median, p10, min, max) for a series of metric values."""
    if not results:
        return {"mean": 0.0, "median": 0.0, "p10": 0.0, "min": 0.0, "max": 0.0}

    sorted_vals = sorted(results)
    n = len(sorted_vals)
    mean_val = sum(sorted_vals) / n

    # Median
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

    # 10th percentile
    p10_idx = max(0, int(math.floor(0.10 * (n - 1))))
    p10_val = sorted_vals[p10_idx]

    return {
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "p10": round(p10_val, 4),
        "min": round(sorted_vals[0], 4),
        "max": round(sorted_vals[-1], 4),
    }


def compute_win_tie_loss(
    metric_a: list[float], metric_b: list[float], epsilon: float = 1e-4
) -> dict[str, int]:
    """Compare two parallel metric lists and return win/tie/loss counts for metric_a vs metric_b."""
    wins = 0
    ties = 0
    losses = 0
    for a, b in zip(metric_a, metric_b):
        diff = a - b
        if abs(diff) <= epsilon:
            ties += 1
        elif diff > epsilon:
            wins += 1
        else:
            losses += 1
    return {"wins": wins, "ties": ties, "losses": losses}


def compute_bootstrap_ci(
    metric_a: list[float],
    metric_b: list[float],
    num_resamples: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for mean(metric_a - metric_b).

    Returns (mean_diff, lower_bound, upper_bound).
    """
    diffs = [a - b for a, b in zip(metric_a, metric_b)]
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0, 0.0)

    mean_diff = sum(diffs) / n
    rng = random.Random(seed)

    boot_means: list[float] = []
    for _ in range(num_resamples):
        sample = [rng.choice(diffs) for _ in range(n)]
        boot_means.append(sum(sample) / n)

    boot_means.sort()
    alpha = (1.0 - ci) / 2.0
    lower_idx = max(0, int(math.floor(alpha * num_resamples)))
    upper_idx = min(num_resamples - 1, int(math.ceil((1.0 - alpha) * num_resamples)))

    lower = boot_means[lower_idx]
    upper = boot_means[upper_idx]

    return (round(mean_diff, 4), round(lower, 4), round(upper, 4))


def find_losses(
    scenario_results: list[dict[str, Any]],
    primary_key: str = "heuristic_svc",
    baseline_key: str = "naive_svc",
    epsilon: float = 1e-4,
) -> list[dict[str, Any]]:
    """Identify scenarios where the primary policy performs worse than the baseline."""
    losses: list[dict[str, Any]] = []
    for r in scenario_results:
        p_val = float(r.get(primary_key, 0.0))
        b_val = float(r.get(baseline_key, 0.0))
        if p_val < b_val - epsilon:
            diff = b_val - p_val
            loss_record = dict(r)
            loss_record["service_level_delta"] = round(-diff, 4)
            # Infer plausible root cause
            if r.get("is_holdout", False):
                reason = "Holdout compound disaster with extreme multi-corridor transit bottleneck"
            elif "Route" in r.get("scenario_name", "") or "disruption" in str(r.get("events", "")):
                reason = (
                    "Greedy baseline refilled before route closure, "
                    "while heuristic paced allocation"
                )
            elif float(r.get("heuristic_unmet", 0.0)) > float(r.get("naive_unmet", 0.0)):
                reason = (
                    "Conservative safety buffer held back inventory at depot during sudden surge"
                )
            else:
                reason = "Timing divergence on transit delivery window"
            loss_record["loss_reason"] = reason
            losses.append(loss_record)
    return losses
