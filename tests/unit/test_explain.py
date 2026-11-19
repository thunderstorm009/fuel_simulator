import json
from datetime import datetime
from pathlib import Path

from core.explain import build_explanation
from core.models import FuelType, Snapshot, SupplyArrivalStatus
from core.policies.heuristic import HeuristicPolicy
from core.risk import ForecastRecord, forecast_pair

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def snapshot_fixture() -> Snapshot:
    raw = {
        name: json.loads((SAMPLES / f"{name}.json").read_text())
        for name in (
            "instance",
            "regions",
            "depots",
            "stations",
            "routes",
            "supply-arrivals",
            "events",
            "metrics",
        )
    }
    raw["supply_arrivals"] = raw.pop("supply-arrivals")
    raw.update(
        allocations=[],
        demand_history=[],
        fetched_at="2026-01-01T00:00:00Z",
        stale=False,
        data_status="HEALTHY",
    )
    return Snapshot.model_validate(raw)


def urgent_forecast(snapshot: Snapshot) -> ForecastRecord:
    station = next(row for row in snapshot.stations if row.id == "station-mirpur")
    station.inventory[FuelType.DIESEL] = 3000
    return forecast_pair(snapshot, station, FuelType.DIESEL, seed=42)


def test_explanation_reruns_forecast_with_proposed_arrival() -> None:
    snapshot = snapshot_fixture()
    before = urgent_forecast(snapshot)
    plan = HeuristicPolicy().recommend(snapshot, [before])[0]
    delayed = next(row for row in snapshot.supply_arrivals if row.id == "supply-201")
    delayed.status = SupplyArrivalStatus.DELAYED
    delayed.planned_tick += 5

    explanation = build_explanation(snapshot, plan, before)

    assert (
        explanation["risk_before"]["stockout_probability_24h"]
        >= explanation["risk_after"]["stockout_probability_24h"]
    )
    severity = {"ok": 0, "medium": 1, "high": 2, "critical": 3}
    assert (
        severity[explanation["risk_before"]["risk_level"]]
        >= severity[explanation["risk_after"]["risk_level"]]
    )
    assert explanation["drivers"]["delayed_supply"][0]["planned_tick"] == delayed.planned_tick
    assert explanation["policy_used"] == "heuristic"
    assert explanation["data_status"] == "HEALTHY"
    assert datetime.fromisoformat(explanation["created_at"].replace("Z", "+00:00")) == (
        snapshot.fetched_at
    )
