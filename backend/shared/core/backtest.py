"""Pure demand backtesting, calibration evaluation, and experiment logging."""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.forecast import calibrate_ratio, expected_demand
from core.models import DemandObs
from core.version import MODEL_VERSION, POLICY_VERSION
from core.world import PROFILE_NOISE


@dataclass(frozen=True)
class HorizonMetrics:
    horizon_name: str
    horizon_ticks: int
    horizon_hours: float
    sample_count: int
    mape: float
    bias: float
    interval_coverage: float


@dataclass(frozen=True)
class SeriesBacktest:
    station_id: str
    fuel_type: str
    profile: str
    horizons: dict[str, HorizonMetrics]


@dataclass(frozen=True)
class CalibrationBucket:
    bucket_label: str
    min_prob: float
    max_prob: float
    count: int
    predicted_avg: float
    observed_rate: float


@dataclass(frozen=True)
class BacktestSummary:
    model_version: str
    policy_version: str
    evaluated_at: str
    series: list[SeriesBacktest]
    aggregate: dict[str, HorizonMetrics]
    aggregate_inside_events: dict[str, HorizonMetrics] | None = None
    aggregate_outside_events: dict[str, HorizonMetrics] | None = None
    brier_score: float = 0.0
    reliability_buckets: list[CalibrationBucket] | None = None


def compute_brier_score(
    predictions: Sequence[float],
    actuals: Sequence[int | bool | float],
) -> float:
    """Compute Brier score (mean squared error of probabilistic forecasts)."""
    if len(predictions) != len(actuals):
        raise ValueError("predictions and actuals must have the same length")
    if not predictions:
        return 0.0

    total_sq_err = sum((float(p) - (1.0 if a else 0.0)) ** 2 for p, a in zip(predictions, actuals))
    return round(total_sq_err / len(predictions), 4)


def evaluate_probability_reliability(
    predictions_and_outcomes: Sequence[tuple[float, bool]],
    num_buckets: int = 5,
) -> list[CalibrationBucket]:
    """Bucket predicted P(stockout 24h) and compare with realized outcomes."""
    if num_buckets <= 0:
        raise ValueError("num_buckets must be positive")

    step = 1.0 / num_buckets
    buckets_def = [
        (f"{i * step:.1f} - {(i + 1) * step:.1f}", i * step, (i + 1) * step)
        for i in range(num_buckets)
    ]

    results: list[CalibrationBucket] = []
    for label, min_p, max_p in buckets_def:
        items = [
            (prob, outcome)
            for prob, outcome in predictions_and_outcomes
            if min_p <= prob < max_p or (max_p >= 1.0 and prob >= 1.0)
        ]
        count = len(items)
        if count > 0:
            pred_avg = sum(p for p, _ in items) / count
            obs_rate = sum(1 for _, out in items if out) / count
        else:
            pred_avg = (min_p + max_p) / 2.0
            obs_rate = 0.0

        results.append(
            CalibrationBucket(
                bucket_label=label,
                min_prob=round(min_p, 2),
                max_prob=round(max_p, 2),
                count=count,
                predicted_avg=round(pred_avg, 3),
                observed_rate=round(obs_rate, 3),
            )
        )
    return results


def measure_spike_convergence_ticks(
    observations: Sequence[dict[str, Any]],
    spike_tick: int,
    spike_multiplier: float,
    profile: str,
    fuel: Any,
    model_version: str = "1.2.0",
    tick_minutes: int = 15,
    tolerance: float = 0.05,
) -> int:
    """Measure ticks required for forecast to converge within tolerance after demand spike."""
    fuel_str = getattr(fuel, "value", str(fuel))
    obs_by_tick = {int(o["tick"]): o for o in observations}
    max_tick = max(obs_by_tick.keys())

    is_event_aware = model_version >= "1.2.0"

    for t in range(spike_tick, max_tick + 1):
        past_ticks = list(range(max(0, t - 12), t))
        if not past_ticks:
            continue
        past_obs = [obs_by_tick[i] for i in past_ticks]
        observed_past = [float(p["demand_liters"]) for p in past_obs]

        if is_event_aware:
            expected_past = [
                expected_demand(
                    profile,
                    fuel_str,
                    p["sim_time"],
                    multiplier=float(p.get("multiplier", 1.0)),
                    tick_minutes=tick_minutes,
                )
                for p in past_obs
            ]
            ratio = calibrate_ratio(observed_past, expected_past)
            current_mult = float(obs_by_tick[t].get("multiplier", spike_multiplier))
            predicted = expected_demand(
                profile,
                fuel_str,
                obs_by_tick[t]["sim_time"],
                multiplier=current_mult * ratio,
                tick_minutes=tick_minutes,
            )
        else:
            expected_past = [
                expected_demand(
                    profile,
                    fuel_str,
                    p["sim_time"],
                    multiplier=1.0,
                    tick_minutes=tick_minutes,
                )
                for p in past_obs
            ]
            ratio = calibrate_ratio(observed_past, expected_past)
            predicted = expected_demand(
                profile,
                fuel_str,
                obs_by_tick[t]["sim_time"],
                multiplier=ratio,
                tick_minutes=tick_minutes,
            )

        actual = float(obs_by_tick[t]["demand_liters"])
        if actual > 0:
            rel_err = abs(predicted - actual) / actual
            if rel_err <= tolerance:
                return t - spike_tick

    return max_tick - spike_tick


def run_backtest(
    records: Sequence[DemandObs | dict[str, Any]],
    station_profiles: dict[str, str],
    horizons: dict[str, int] | None = None,
    tick_minutes: int = 15,
    model_version: str = MODEL_VERSION,
    policy_version: str = POLICY_VERSION,
    evaluated_at: str | None = None,
) -> BacktestSummary:
    """Evaluate demand forecasting accuracy against historical demand observations."""
    if horizons is None:
        horizons = {
            "1h": 4,
            "6h": 24,
            "12h": 48,
            "24h": 96,
        }

    is_event_aware = model_version >= "1.2.0"

    # Group records by (station_id, fuel_type)
    series_map: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in records:
        if isinstance(r, dict):
            station_id = r["station_id"]
            fuel = r["fuel_type"]
            fuel_str = getattr(fuel, "value", str(fuel))
            tick = int(r["tick"])
            sim_time_val = r["sim_time"]
            if isinstance(sim_time_val, str):
                sim_time = datetime.fromisoformat(sim_time_val)
            else:
                sim_time = sim_time_val
            demand_liters = float(r["demand_liters"])
            multiplier = float(r.get("multiplier", 1.0))
        else:
            station_id = r.station_id
            fuel_str = r.fuel_type.value
            tick = r.tick
            sim_time = r.sim_time
            demand_liters = r.demand_liters
            multiplier = getattr(r, "multiplier", 1.0)

        series_map.setdefault((station_id, fuel_str), []).append(
            {
                "tick": tick,
                "sim_time": sim_time,
                "demand_liters": demand_liters,
                "multiplier": multiplier,
            }
        )

    series_results: list[SeriesBacktest] = []
    agg_errors: dict[str, list[tuple[float, float, bool]]] = {h: [] for h in horizons}
    agg_errors_inside: dict[str, list[tuple[float, float, bool]]] = {h: [] for h in horizons}
    agg_errors_outside: dict[str, list[tuple[float, float, bool]]] = {h: [] for h in horizons}

    for (station_id, fuel_str), obs_list in sorted(series_map.items()):
        obs_sorted = sorted(obs_list, key=lambda x: x["tick"])
        profile = station_profiles.get(station_id, "urban_high")
        noise = PROFILE_NOISE.get(profile, 0.10)

        horizons_metrics: dict[str, HorizonMetrics] = {}
        for h_name, h_ticks in horizons.items():
            h_hours = (h_ticks * tick_minutes) / 60.0
            apes: list[float] = []
            biases: list[float] = []
            covered_list: list[bool] = []

            min_history = 4
            for i in range(min_history, len(obs_sorted) - h_ticks + 1):
                past = obs_sorted[max(0, i - 12) : i]
                future = obs_sorted[i : i + h_ticks]

                observed_past = [p["demand_liters"] for p in past]
                if is_event_aware:
                    expected_past = [
                        expected_demand(
                            profile,
                            fuel_str,
                            p["sim_time"],
                            multiplier=p.get("multiplier", 1.0),
                            tick_minutes=tick_minutes,
                        )
                        for p in past
                    ]
                else:
                    expected_past = [
                        expected_demand(
                            profile,
                            fuel_str,
                            p["sim_time"],
                            multiplier=1.0,
                            tick_minutes=tick_minutes,
                        )
                        for p in past
                    ]

                ratio = calibrate_ratio(observed_past, expected_past)

                if is_event_aware:
                    expected_future_sum = sum(
                        expected_demand(
                            profile,
                            fuel_str,
                            f["sim_time"],
                            multiplier=f.get("multiplier", 1.0) * ratio,
                            tick_minutes=tick_minutes,
                        )
                        for f in future
                    )
                else:
                    expected_future_sum = sum(
                        expected_demand(
                            profile,
                            fuel_str,
                            f["sim_time"],
                            multiplier=ratio,
                            tick_minutes=tick_minutes,
                        )
                        for f in future
                    )

                actual_future_sum = sum(f["demand_liters"] for f in future)

                if actual_future_sum > 0:
                    ape = abs(actual_future_sum - expected_future_sum) / actual_future_sum
                    bias = (expected_future_sum - actual_future_sum) / actual_future_sum
                else:
                    ape = 0.0
                    bias = 0.0

                sigma_future = expected_future_sum * (noise / math.sqrt(max(1, h_ticks)))
                p10 = max(0.0, expected_future_sum - 1.282 * sigma_future)
                p90 = expected_future_sum + 1.282 * sigma_future
                is_covered = p10 <= actual_future_sum <= p90

                apes.append(ape)
                biases.append(bias)
                covered_list.append(is_covered)
                agg_errors[h_name].append((ape, bias, is_covered))

                # Segment into inside-event vs outside-event
                is_inside_event = any(abs(f.get("multiplier", 1.0) - 1.0) > 1e-4 for f in future)
                if is_inside_event:
                    agg_errors_inside[h_name].append((ape, bias, is_covered))
                else:
                    agg_errors_outside[h_name].append((ape, bias, is_covered))

            if apes:
                mean_mape = sum(apes) / len(apes)
                mean_bias = sum(biases) / len(biases)
                coverage = sum(1 for c in covered_list if c) / len(covered_list)
            else:
                mean_mape = 0.0
                mean_bias = 0.0
                coverage = 1.0

            horizons_metrics[h_name] = HorizonMetrics(
                horizon_name=h_name,
                horizon_ticks=h_ticks,
                horizon_hours=h_hours,
                sample_count=len(apes),
                mape=round(mean_mape, 4),
                bias=round(mean_bias, 4),
                interval_coverage=round(coverage, 4),
            )

        series_results.append(
            SeriesBacktest(
                station_id=station_id,
                fuel_type=fuel_str,
                profile=profile,
                horizons=horizons_metrics,
            )
        )

    # Compute global aggregates
    aggregate_metrics: dict[str, HorizonMetrics] = {}
    aggregate_inside: dict[str, HorizonMetrics] = {}
    aggregate_outside: dict[str, HorizonMetrics] = {}

    for h_name, errors in agg_errors.items():
        h_ticks = horizons[h_name]
        h_hours = (h_ticks * tick_minutes) / 60.0
        if errors:
            m_mape = sum(e[0] for e in errors) / len(errors)
            m_bias = sum(e[1] for e in errors) / len(errors)
            cov = sum(1 for e in errors if e[2]) / len(errors)
        else:
            m_mape, m_bias, cov = 0.0, 0.0, 1.0

        aggregate_metrics[h_name] = HorizonMetrics(
            horizon_name=h_name,
            horizon_ticks=h_ticks,
            horizon_hours=h_hours,
            sample_count=len(errors),
            mape=round(m_mape, 4),
            bias=round(m_bias, 4),
            interval_coverage=round(cov, 4),
        )

    for h_name, errors in agg_errors_inside.items():
        h_ticks = horizons[h_name]
        h_hours = (h_ticks * tick_minutes) / 60.0
        if errors:
            m_mape = sum(e[0] for e in errors) / len(errors)
            m_bias = sum(e[1] for e in errors) / len(errors)
            cov = sum(1 for e in errors if e[2]) / len(errors)
        else:
            m_mape, m_bias, cov = 0.0, 0.0, 1.0
        aggregate_inside[h_name] = HorizonMetrics(
            horizon_name=h_name,
            horizon_ticks=h_ticks,
            horizon_hours=h_hours,
            sample_count=len(errors),
            mape=round(m_mape, 4),
            bias=round(m_bias, 4),
            interval_coverage=round(cov, 4),
        )

    for h_name, errors in agg_errors_outside.items():
        h_ticks = horizons[h_name]
        h_hours = (h_ticks * tick_minutes) / 60.0
        if errors:
            m_mape = sum(e[0] for e in errors) / len(errors)
            m_bias = sum(e[1] for e in errors) / len(errors)
            cov = sum(1 for e in errors if e[2]) / len(errors)
        else:
            m_mape, m_bias, cov = 0.0, 0.0, 1.0
        aggregate_outside[h_name] = HorizonMetrics(
            horizon_name=h_name,
            horizon_ticks=h_ticks,
            horizon_hours=h_hours,
            sample_count=len(errors),
            mape=round(m_mape, 4),
            bias=round(m_bias, 4),
            interval_coverage=round(cov, 4),
        )

    return BacktestSummary(
        model_version=model_version,
        policy_version=policy_version,
        evaluated_at=evaluated_at or datetime.now(timezone.utc).isoformat(),
        series=series_results,
        aggregate=aggregate_metrics,
        aggregate_inside_events=aggregate_inside,
        aggregate_outside_events=aggregate_outside,
    )


def evaluate_stockout_calibration(
    predictions_and_outcomes: Sequence[tuple[float, bool]],
) -> list[CalibrationBucket]:
    """Bucket predicted P(stockout 24h) and compare with realized stockout frequency."""
    return evaluate_probability_reliability(predictions_and_outcomes, num_buckets=5)


def append_experiment_log(
    file_path: Path,
    git_sha: str,
    model_version: str,
    policy_version: str,
    scenario: str,
    policy: str,
    service_level: float,
    unmet_liters: float,
    mape: float,
    date_str: str | None = None,
) -> None:
    """Append a validated run result row to experiments.csv."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = file_path.exists()
    header = [
        "date",
        "git_sha",
        "model_version",
        "policy_version",
        "scenario",
        "policy",
        "service_level",
        "unmet_liters",
        "mape",
    ]

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(
            [
                date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                git_sha,
                model_version,
                policy_version,
                scenario,
                policy,
                f"{service_level:.4f}",
                f"{unmet_liters:.1f}",
                f"{mape:.4f}",
            ]
        )
