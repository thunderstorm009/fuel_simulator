"""Unit tests for the scenario runner and scenario definitions."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "scripts"))
sys.path.insert(0, str(ROOT_DIR / "backend" / "shared"))

from scenario_runner import (  # noqa: E402
    NaivePolicy,
    NonePolicy,
    ScenarioMetrics,
    load_scenario_events,
)


def test_none_policy_always_empty():
    policy = NonePolicy()
    assert policy.name == "none"
    snap = SimpleNamespace(stations=[], depots=[], routes=[], allocations=[])
    assert policy.recommend(snap, []) == []


def test_naive_policy_refills_low_inventory():
    policy = NaivePolicy()
    assert policy.name == "naive"

    from core.models import FuelType, RouteStatus

    # Station with 10% inventory (below 30% threshold)
    station = SimpleNamespace(
        id="station-1",
        capacity={FuelType.DIESEL: 10000.0},
        inventory={FuelType.DIESEL: 1000.0},
    )
    depot = SimpleNamespace(
        id="depot-1",
        inventory={FuelType.DIESEL: 20000.0},
    )
    route = SimpleNamespace(
        id="route-1",
        source_depot_id="depot-1",
        destination_station_id="station-1",
        status=RouteStatus.AVAILABLE,
        max_shipment=5000.0,
        transit_ticks=2,
    )
    snapshot = SimpleNamespace(
        instance=SimpleNamespace(tick=10),
        stations=[station],
        depots=[depot],
        routes=[route],
        allocations=[],
    )

    plans = policy.recommend(snapshot, [])
    assert len(plans) == 1
    assert plans[0].request.destination_station_id == "station-1"
    assert plans[0].request.quantity == 5000.0  # capped by max_shipment


def test_scenario_yaml_definitions():
    scenarios_dir = ROOT_DIR / "scenarios"
    for name in ("baseline", "spike", "route", "combined"):
        yaml_path = scenarios_dir / f"{name}.yaml"
        assert yaml_path.exists(), f"missing {name}.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
            assert "name" in data
            assert "events" in data
            assert isinstance(data["events"], list)


def test_load_scenario_events():
    events = load_scenario_events("spike")
    assert len(events) >= 1
    assert events[0]["type"] == "demand_spike"


def test_scenario_metrics_dataclass():
    m = ScenarioMetrics(
        scenario="baseline",
        policy="heuristic",
        run=1,
        ticks=20,
        service_level=0.95,
        unmet_demand_liters=500.0,
        served_demand_liters=9500.0,
        allocation_liters=4000.0,
        allocation_failures=0,
        station_tick_stockouts=1,
        elapsed_seconds=1.2,
    )
    assert m.service_level == 0.95
    assert m.scenario == "baseline"
