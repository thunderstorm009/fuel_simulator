"""Unit tests for pure demand backtesting and experiment logging."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from core.backtest import (
    append_experiment_log,
    evaluate_stockout_calibration,
    run_backtest,
)
from core.models import DemandObs, FuelType
from core.world import DAILY_LITERS


def test_backtest_deterministic_on_fixture(tmp_path: Path) -> None:
    # Construct a synthetic 20-tick history for station-mirpur DIESEL
    profile = "urban_high"
    daily = DAILY_LITERS[profile]["DIESEL"]
    tick_minutes = 15
    per_tick = daily / (1440 / tick_minutes)

    records: list[DemandObs] = []
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    for t in range(1, 25):
        records.append(
            DemandObs(
                id=t,
                station_id="station-mirpur",
                fuel_type=FuelType.DIESEL,
                tick=t,
                sim_time=base_time,
                demand_liters=per_tick,
                served_liters=per_tick,
                unmet_liters=0.0,
            )
        )

    summary = run_backtest(
        records,
        station_profiles={"station-mirpur": profile},
        horizons={"1h": 4, "2h": 8},
        tick_minutes=tick_minutes,
        model_version="1.1.0",
        policy_version="2.0.0",
    )

    assert summary.model_version == "1.1.0"
    assert summary.policy_version == "2.0.0"
    assert "1h" in summary.aggregate
    assert "2h" in summary.aggregate
    h1 = summary.aggregate["1h"]
    assert h1.sample_count > 0
    # On flat expected synthetic demand without noise, MAPE should be very low
    assert h1.mape < 0.35
    assert h1.interval_coverage >= 0.0


def test_evaluate_stockout_calibration() -> None:
    pairs = [
        (0.05, False),
        (0.10, False),
        (0.45, True),
        (0.50, False),
        (0.85, True),
        (0.95, True),
    ]
    buckets = evaluate_stockout_calibration(pairs)
    assert len(buckets) == 5
    b_low = buckets[0]
    assert b_low.bucket_label == "0.0 - 0.2"
    assert b_low.count == 2
    assert b_low.observed_rate == 0.0

    b_high = buckets[4]
    assert b_high.bucket_label == "0.8 - 1.0"
    assert b_high.count == 2
    assert b_high.observed_rate == 1.0


def test_append_experiment_log(tmp_path: Path) -> None:
    csv_file = tmp_path / "experiments.csv"
    append_experiment_log(
        csv_file,
        git_sha="abcdef1",
        model_version="1.1.0",
        policy_version="2.0.0",
        scenario="test_sc",
        policy="heuristic",
        service_level=0.995,
        unmet_liters=120.0,
        mape=0.032,
    )

    assert csv_file.exists()
    with open(csv_file, encoding="utf-8") as f:
        reader = list(csv.reader(f))
    assert len(reader) == 2  # header + 1 row
    assert reader[0][1] == "git_sha"
    assert reader[1][1] == "abcdef1"
    assert reader[1][2] == "1.1.0"
    assert reader[1][3] == "2.0.0"
    assert reader[1][4] == "test_sc"
