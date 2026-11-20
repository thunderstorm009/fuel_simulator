import json
from pathlib import Path

from core.models import Allocation, Forecast, FuelType, RiskLevel, Snapshot
from core.policies.heuristic import HeuristicPolicy
from core.risk import ForecastRecord, TrajectoryPoint

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


def urgent_forecast(snapshot: Snapshot, station_id: str, fuel: FuelType) -> ForecastRecord:
    station = next(row for row in snapshot.stations if row.id == station_id)
    inventory = station.inventory[fuel]
    trajectory = [
        TrajectoryPoint(
            offset,
            max(0, inventory - 50 * offset),
            max(0, inventory - 50 * offset),
            max(0, inventory - 50 * offset),
        )
        for offset in range(97)
    ]
    forecast = Forecast(
        station_id=station_id,
        fuel_type=fuel,
        hours_to_stockout=6.0,
        p10_hours=5.0,
        p50_hours=6.0,
        p90_hours=7.0,
        stockout_probability_24h=0.9,
        confidence=0.9,
        risk_level=RiskLevel.CRITICAL,
        needs_review=False,
    )
    return ForecastRecord(
        forecast=forecast,
        trajectory=trajectory,
        drivers={"demand_multiplier": station.demand_multiplier, "recent_ratio": 1.0},
    )


def test_no_risk_produces_no_recommendations() -> None:
    assert HeuristicPolicy().recommend(snapshot_fixture(), []) == []


def test_one_critical_pair_produces_a_feasible_recommendation() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000

    result = HeuristicPolicy().recommend(
        snapshot, [urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)]
    )

    assert len(result) == 1
    assert result[0].request.destination_station_id == mirpur.id
    assert result[0].request.quantity <= 7000


def test_estimated_arrival_matches_simulator_dispatch_tick_semantics() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000

    forecast = urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)
    result = HeuristicPolicy().recommend(snapshot, [forecast])

    route = next(row for row in snapshot.routes if row.id == result[0].request.route_id)
    assert result[0].arrival_tick == snapshot.instance.tick + route.transit_ticks
    assert (
        result[0].projected_inventory_at_arrival
        == forecast.trajectory[route.transit_ticks].mean_inventory
    )


def test_disrupted_route_uses_an_available_alternative() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000
    snapshot.routes[0].status = "DISRUPTED"

    result = HeuristicPolicy().recommend(
        snapshot, [urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)]
    )

    assert result
    assert all(item.request.route_id == "route-patiya-mirpur" for item in result)


def test_depot_shortage_uses_an_alternative_depot() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000
    snapshot.depots[0].inventory[FuelType.DIESEL] = 0

    result = HeuristicPolicy().recommend(
        snapshot, [urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)]
    )

    assert result
    assert all(item.request.source_depot_id == "depot-patiya" for item in result)


def test_in_transit_allocation_suppresses_duplicate_recommendation() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000
    snapshot.allocations = [
        Allocation.model_validate(
            {
                "id": 1,
                "idempotency_key": "existing",
                "source_depot_id": "depot-gazipur",
                "destination_station_id": mirpur.id,
                "route_id": "route-gazipur-mirpur",
                "fuel_type": "DIESEL",
                "quantity": 3000,
                "created_tick": snapshot.instance.tick,
                "departure_tick": snapshot.instance.tick,
                "expected_arrival_tick": snapshot.instance.tick + 2,
                "actual_arrival_tick": None,
                "status": "IN_TRANSIT",
                "failure_reason": None,
            }
        )
    ]

    result = HeuristicPolicy().recommend(
        snapshot, [urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)]
    )

    assert result == []


def test_split_shipments_respect_route_and_dispatch_limits() -> None:
    snapshot = snapshot_fixture()
    tongi = next(row for row in snapshot.stations if row.id == "station-tongi")
    tongi.inventory[FuelType.DIESEL] = 100
    forecast = urgent_forecast(snapshot, tongi.id, FuelType.DIESEL)
    snapshot.depots[0].inventory[FuelType.DIESEL] = 20000

    result = HeuristicPolicy().recommend(snapshot, [forecast])

    assert len(result) >= 2
    assert all(item.request.quantity <= 6500 for item in result)
    assert sum(item.request.quantity for item in result) <= 12000


def test_same_inputs_produce_same_economic_recommendations() -> None:
    snapshot = snapshot_fixture()
    mirpur = next(row for row in snapshot.stations if row.id == "station-mirpur")
    mirpur.inventory[FuelType.DIESEL] = 3000
    forecasts = [urgent_forecast(snapshot, mirpur.id, FuelType.DIESEL)]
    policy = HeuristicPolicy()

    first = policy.recommend(snapshot, forecasts)
    second = policy.recommend(snapshot, forecasts)

    def fields(rows):
        return [
            (
                row.request.source_depot_id,
                row.request.destination_station_id,
                row.request.route_id,
                row.request.quantity,
            )
            for row in rows
        ]

    assert fields(first) == fields(second)
