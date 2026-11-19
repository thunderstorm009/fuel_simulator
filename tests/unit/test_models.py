import httpx
import pytest
from pydantic import ValidationError

from core.models import (
    Allocation,
    AllocationStatus,
    DataStatus,
    Depot,
    FuelType,
    Instance,
    Route,
    Station,
    parse_sim_error,
)


def test_instance_uses_simulator_field_names_and_ignores_extra_fields() -> None:
    instance = Instance.model_validate(
        {
            "id": 1,
            "scenario_id": "baseline",
            "scenario_version": "1.0",
            "seed": 12345,
            "sim_time": "2026-01-01T00:00:00+00:00",
            "tick": 4,
            "tick_minutes": 15,
            "status": "PAUSED",
            "future_field": True,
        }
    )
    assert instance.tick_minutes == 15
    assert instance.model_dump().get("future_field") is None


def test_station_requires_known_fields_and_enum_values() -> None:
    station = Station.model_validate(
        {
            "id": "station-mirpur",
            "name": "Mirpur Fuel Station",
            "region_id": "region-dhaka",
            "status": "OPEN",
            "demand_profile": "urban_high",
            "demand_multiplier": 1.0,
            "capacity": {"DIESEL": 15000, "PETROL": 14000, "OCTANE": 9000},
            "inventory": {"DIESEL": 9000, "PETROL": 9000, "OCTANE": 5000},
        }
    )
    assert station.inventory[FuelType.DIESEL] == 9000
    with pytest.raises(ValidationError):
        Station.model_validate({"id": "station-mirpur"})


def test_route_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        Route.model_validate(
            {
                "id": "route-gazipur-mirpur",
                "source_depot_id": "depot-gazipur",
                "destination_station_id": "station-mirpur",
                "transit_ticks": 2,
                "max_shipment": 7000,
                "status": "BROKEN",
            }
        )


def test_allocation_and_snapshot_enums_are_typed() -> None:
    allocation = Allocation.model_validate(
        {
            "id": 1,
            "idempotency_key": "demo-001",
            "source_depot_id": "depot-gazipur",
            "destination_station_id": "station-mirpur",
            "route_id": "route-gazipur-mirpur",
            "fuel_type": "DIESEL",
            "quantity": 3000,
            "created_tick": 5,
            "departure_tick": None,
            "expected_arrival_tick": None,
            "actual_arrival_tick": None,
            "status": "PENDING",
            "failure_reason": None,
        }
    )
    assert allocation.status is AllocationStatus.PENDING
    assert DataStatus.HEALTHY.value == "HEALTHY"


def test_depot_wrong_inventory_value_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Depot.model_validate(
            {
                "id": "depot-gazipur",
                "name": "Gazipur Depot",
                "region_id": "region-dhaka",
                "status": "OPEN",
                "dispatch_capacity_per_tick": 12000,
                "capacity": {"DIESEL": 90000, "PETROL": 70000, "OCTANE": 45000},
                "inventory": {"DIESEL": "lots", "PETROL": 45000, "OCTANE": 26000},
            }
        )


@pytest.mark.parametrize(
    ("status", "payload", "code"),
    [
        (
            409,
            {"detail": {"code": "ROUTE_DISRUPTED", "message": "route unavailable"}},
            "ROUTE_DISRUPTED",
        ),
        (503, {"error": {"code": "FAULT_INJECTED", "message": "temporary"}}, "FAULT_INJECTED"),
        (503, {"detail": {"code": "FAULT_INJECTED"}}, "FAULT_INJECTED"),
        (
            422,
            {"detail": [{"loc": ["body", "quantity"], "msg": "greater than 0"}]},
            "VALIDATION_ERROR",
        ),
    ],
)
def test_parse_sim_error_shapes(status: int, payload: dict, code: str) -> None:
    error = parse_sim_error(httpx.Response(status, json=payload))
    assert error.status_code == status
    assert error.code == code


def test_parse_sim_error_handles_non_json_response() -> None:
    error = parse_sim_error(httpx.Response(503, text="upstream unavailable"))
    assert error.status_code == 503
    assert error.code == "UNKNOWN_ERROR"
