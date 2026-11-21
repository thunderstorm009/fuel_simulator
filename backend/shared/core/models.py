"""Validated models for the official simulator contract and internal records."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from httpx import Response
from pydantic import BaseModel, ConfigDict, Field

from core.version import MODEL_VERSION, POLICY_VERSION


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class FuelType(str, Enum):
    DIESEL = "DIESEL"
    PETROL = "PETROL"
    OCTANE = "OCTANE"


class InstanceStatus(str, Enum):
    PAUSED = "PAUSED"
    RUNNING = "RUNNING"


class DepotStatus(str, Enum):
    OPEN = "OPEN"
    CONSTRAINED = "CONSTRAINED"


class StationStatus(str, Enum):
    OPEN = "OPEN"
    OUTAGE = "OUTAGE"


class RouteStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DISRUPTED = "DISRUPTED"


class SupplyArrivalStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    ARRIVED = "ARRIVED"


class SimEventType(str, Enum):
    DEMAND_SPIKE = "demand_spike"
    ROUTE_DISRUPTION = "route_disruption"
    STATION_OUTAGE = "station_outage"
    DEPOT_CONSTRAINT = "depot_constraint"
    SHIPMENT_DELAY = "shipment_delay"
    SUPPLY_SHORTFALL = "supply_shortfall"


class SimEventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class AllocationStatus(str, Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RecommendationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED = "ARRIVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    OK = "ok"


class DataStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class Instance(ContractModel):
    id: int
    scenario_id: str
    scenario_version: str
    seed: int
    sim_time: datetime
    tick: int
    tick_minutes: int
    status: InstanceStatus


class Region(ContractModel):
    id: str
    name: str
    demand_factor: float


class Depot(ContractModel):
    id: str
    name: str
    region_id: str
    status: DepotStatus
    dispatch_capacity_per_tick: float
    capacity: dict[FuelType, float]
    inventory: dict[FuelType, float]


class Station(ContractModel):
    id: str
    name: str
    region_id: str
    status: StationStatus
    demand_profile: str
    demand_multiplier: float
    capacity: dict[FuelType, float]
    inventory: dict[FuelType, float]


class Route(ContractModel):
    id: str
    source_depot_id: str
    destination_station_id: str
    transit_ticks: int
    max_shipment: float
    status: RouteStatus


class SupplyArrival(ContractModel):
    id: str
    depot_id: str
    fuel_type: FuelType
    quantity: float
    planned_tick: int
    actual_tick: Optional[int]
    status: SupplyArrivalStatus


class SimEvent(ContractModel):
    id: int
    type: SimEventType
    start_tick: int
    end_tick: int
    status: SimEventStatus
    parameters: dict[str, Any] = Field(default_factory=dict)


class Allocation(ContractModel):
    id: int
    idempotency_key: str = Field(min_length=1, max_length=150)
    source_depot_id: str
    destination_station_id: str
    route_id: str
    fuel_type: FuelType
    quantity: float = Field(gt=0)
    created_tick: int
    departure_tick: Optional[int]
    expected_arrival_tick: Optional[int]
    actual_arrival_tick: Optional[int]
    status: AllocationStatus
    failure_reason: Optional[str]


class AllocationTerms(ContractModel):
    """Allocation fields before the worker assigns its permanent idempotency key."""

    source_depot_id: str
    destination_station_id: str
    route_id: str
    fuel_type: FuelType
    quantity: float = Field(gt=0)


class AllocationRequest(AllocationTerms):
    """Exact allocation body sent to the simulator."""

    idempotency_key: str = Field(min_length=1, max_length=150)


class DemandObs(ContractModel):
    id: int
    station_id: str
    fuel_type: FuelType
    tick: int
    sim_time: datetime
    demand_liters: float
    served_liters: float
    unmet_liters: float


class Metrics(ContractModel):
    served_demand_liters: float
    unmet_demand_liters: float
    service_level: float
    allocation_liters: float
    allocation_failures: int


class Forecast(ContractModel):
    station_id: str
    fuel_type: FuelType
    hours_to_stockout: Optional[float]
    p10_hours: Optional[float]
    p50_hours: Optional[float]
    p90_hours: Optional[float]
    stockout_probability_24h: float
    confidence: float
    risk_level: RiskLevel
    needs_review: bool
    model_version: str = MODEL_VERSION


class Explanation(ContractModel):
    drivers: dict[str, Any] = Field(default_factory=dict)
    constraints_applied: list[dict[str, Any]] = Field(default_factory=list)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    triage: dict[str, Any] = Field(default_factory=dict)
    risk_before: dict[str, Any] = Field(default_factory=dict)
    risk_after: dict[str, Any] = Field(default_factory=dict)
    policy_used: str
    data_status: DataStatus
    confidence: float
    created_at: datetime
    model_version: str = MODEL_VERSION
    policy_version: str = POLICY_VERSION


class Recommendation(ContractModel):
    id: str
    status: RecommendationStatus
    source_depot_id: str
    destination_station_id: str
    route_id: str
    fuel_type: FuelType
    quantity: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=150)
    explanation: Explanation
    model_version: str = MODEL_VERSION
    policy_version: str = POLICY_VERSION


class Snapshot(ContractModel):
    instance: Instance
    regions: list[Region]
    depots: list[Depot]
    stations: list[Station]
    routes: list[Route]
    supply_arrivals: list[SupplyArrival]
    events: list[SimEvent]
    allocations: list[Allocation]
    demand_history: list[DemandObs]
    metrics: Metrics
    fetched_at: datetime
    stale: bool
    data_status: DataStatus


class SimulatorError(ContractModel):
    status_code: int
    code: str
    message: str
    detail: Optional[Any] = None


def parse_sim_error(response: Response) -> SimulatorError:
    """Normalize all documented simulator error response shapes."""
    try:
        payload = response.json()
    except ValueError:
        payload = None

    code = "UNKNOWN_ERROR"
    message = response.reason_phrase or "Simulator request failed"
    detail: Optional[Any] = None
    if isinstance(payload, dict):
        error = payload.get("error")
        nested = payload.get("detail")
        candidate = error if isinstance(error, dict) else nested
        if isinstance(candidate, dict):
            code = str(candidate.get("code", code))
            message = str(candidate.get("message", message))
            detail = candidate
        elif isinstance(nested, list):
            code = "VALIDATION_ERROR"
            detail = nested
            if nested and isinstance(nested[0], dict):
                message = str(nested[0].get("msg", message))
        elif isinstance(nested, str):
            message = nested
            detail = nested

    return SimulatorError(
        status_code=response.status_code,
        code=code,
        message=message,
        detail=detail,
    )
