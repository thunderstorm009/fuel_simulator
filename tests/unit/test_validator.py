import json
from pathlib import Path

import pytest

from core.models import Allocation, AllocationRequest, FuelType, Snapshot
from core.validator import Violation, validate

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


def request(**overrides: object) -> AllocationRequest:
    values: dict[str, object] = {
        "idempotency_key": "rec-test",
        "source_depot_id": "depot-gazipur",
        "destination_station_id": "station-mirpur",
        "route_id": "route-gazipur-mirpur",
        "fuel_type": "DIESEL",
        "quantity": 3000,
    }
    values.update(overrides)
    return AllocationRequest.model_validate(values)


@pytest.mark.parametrize(
    ("mutation", "overrides", "expected_code"),
    [
        ("", {"source_depot_id": "missing-depot"}, "NOT_FOUND"),
        ("", {"destination_station_id": "station-tongi"}, "ROUTE_MISMATCH"),
        ("closed_depot", {}, "DEPOT_CLOSED"),
        ("outage_station", {}, "STATION_CLOSED"),
        ("disrupted_route", {}, "ROUTE_DISRUPTED"),
        ("", {"quantity": 7001}, "ROUTE_CAPACITY_EXCEEDED"),
        ("low_inventory", {"quantity": 1001}, "INSUFFICIENT_INVENTORY"),
        ("", {"quantity": 6500}, "DESTINATION_CAPACITY_EXCEEDED"),
    ],
)
def test_validator_reports_simulator_violations_in_order(
    mutation: str, overrides: dict[str, object], expected_code: str
) -> None:
    snapshot = snapshot_fixture()
    if mutation == "closed_depot":
        snapshot.depots[0].status = "CLOSED"
    elif mutation == "outage_station":
        snapshot.stations[0].status = "OUTAGE"
    elif mutation == "disrupted_route":
        snapshot.routes[0].status = "DISRUPTED"
    elif mutation == "low_inventory":
        snapshot.depots[0].inventory[FuelType.DIESEL] = 1000

    violations = validate(request(**overrides), snapshot)

    assert violations
    assert violations[0].code == expected_code


def test_dispatch_capacity_includes_pending_and_in_flight_allocations_for_this_tick() -> None:
    snapshot = snapshot_fixture()
    snapshot.allocations = [
        Allocation.model_validate(
            {
                "id": 1,
                "idempotency_key": "same-tick",
                "source_depot_id": "depot-gazipur",
                "destination_station_id": "station-tongi",
                "route_id": "route-gazipur-tongi",
                "fuel_type": "PETROL",
                "quantity": 6500,
                "created_tick": snapshot.instance.tick,
                "departure_tick": snapshot.instance.tick,
                "expected_arrival_tick": snapshot.instance.tick + 2,
                "actual_arrival_tick": None,
                "status": "IN_TRANSIT",
                "failure_reason": None,
            }
        ),
    ]

    violations = validate(request(quantity=6500), snapshot)

    assert [violation.code for violation in violations] == ["DISPATCH_CAPACITY_EXCEEDED"]


def test_validator_accounts_for_prior_planning_reservations() -> None:
    snapshot = snapshot_fixture()
    prior = request(quantity=4000)

    violations = validate(request(quantity=3000), snapshot, reservations=[prior])

    assert [violation.code for violation in violations] == ["DESTINATION_CAPACITY_EXCEEDED"]


def test_validator_accepts_feasible_allocation() -> None:
    assert validate(request(), snapshot_fixture()) == []


def test_validator_accepts_exact_idempotency_replay_before_current_constraints() -> None:
    snapshot = snapshot_fixture()
    prior = request()
    snapshot.allocations = [
        Allocation.model_validate(
            {
                "id": 7,
                **prior.model_dump(mode="json"),
                "created_tick": snapshot.instance.tick,
                "departure_tick": None,
                "expected_arrival_tick": None,
                "actual_arrival_tick": None,
                "status": "PENDING",
                "failure_reason": None,
            }
        )
    ]
    snapshot.depots[0].inventory[FuelType.DIESEL] = 0

    assert validate(prior, snapshot) == []


def test_validator_blocks_same_idempotency_key_with_different_body() -> None:
    snapshot = snapshot_fixture()
    prior = request()
    snapshot.allocations = [
        Allocation.model_validate(
            {
                "id": 7,
                **prior.model_dump(mode="json"),
                "created_tick": snapshot.instance.tick,
                "departure_tick": None,
                "expected_arrival_tick": None,
                "actual_arrival_tick": None,
                "status": "PENDING",
                "failure_reason": None,
            }
        )
    ]

    violations = validate(request(quantity=3001), snapshot)

    assert [violation.code for violation in violations] == ["IDEMPOTENCY_KEY_MISMATCH"]


def test_violation_is_immutable_and_explicit() -> None:
    violation = Violation("NOT_FOUND", "source depot missing")

    assert violation.code == "NOT_FOUND"
    assert violation.message == "source depot missing"
