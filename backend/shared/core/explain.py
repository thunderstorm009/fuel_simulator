"""Structured, factual explanations for heuristic allocation candidates."""

from __future__ import annotations

from core.models import Allocation, AllocationStatus, Explanation, Snapshot
from core.policies.base import PolicyPlan
from core.risk import ForecastRecord, forecast_pair


def build_explanation(
    snapshot: Snapshot,
    plan: PolicyPlan,
    before: ForecastRecord,
    *,
    policy_used: str = "heuristic",
) -> dict[str, object]:
    """Re-run the pure forecaster with the proposed station arrival added."""
    proposed_snapshot = snapshot.model_copy(deep=True)
    request = plan.request
    proposed_snapshot.allocations.append(
        Allocation(
            id=max((allocation.id for allocation in proposed_snapshot.allocations), default=0) + 1,
            idempotency_key="explanation-only",
            source_depot_id=request.source_depot_id,
            destination_station_id=request.destination_station_id,
            route_id=request.route_id,
            fuel_type=request.fuel_type,
            quantity=request.quantity,
            created_tick=snapshot.instance.tick,
            departure_tick=snapshot.instance.tick + 1,
            expected_arrival_tick=plan.arrival_tick,
            actual_arrival_tick=None,
            status=AllocationStatus.IN_TRANSIT,
            failure_reason=None,
        )
    )
    station = next(
        row for row in proposed_snapshot.stations if row.id == request.destination_station_id
    )
    pair_offset = (
        sum(station.id.encode("utf-8"))
        + list(type(request.fuel_type)).index(request.fuel_type) * 1009
    )
    seed = (snapshot.instance.seed + snapshot.instance.tick * 9176 + pair_offset) % 2**32
    after = forecast_pair(proposed_snapshot, station, request.fuel_type, seed=seed)
    delayed_supply = [
        {
            "id": arrival.id,
            "planned_tick": arrival.planned_tick,
            "quantity": arrival.quantity,
        }
        for arrival in snapshot.supply_arrivals
        if arrival.depot_id == request.source_depot_id
        and arrival.fuel_type is request.fuel_type
        and arrival.status.value == "DELAYED"
    ]
    explanation = Explanation(
        drivers={
            "hours_to_stockout": before.forecast.hours_to_stockout,
            "demand_multiplier": before.drivers.get("demand_multiplier", 1.0),
            "recent_ratio": before.drivers.get("recent_ratio", 1.0),
            "delayed_supply": delayed_supply,
            "arrival_tick": plan.arrival_tick,
            "quantity_liters": request.quantity,
            "projected_inventory_at_arrival": plan.projected_inventory_at_arrival,
            "target_inventory": plan.target_inventory,
        },
        constraints_applied=plan.constraints_applied,
        alternatives=plan.alternatives,
        triage=plan.triage,
        risk_before=_risk_summary(before),
        risk_after=_risk_summary(after),
        policy_used=policy_used,
        data_status=snapshot.data_status,
        confidence=before.forecast.confidence,
        created_at=snapshot.fetched_at,
    )
    return explanation.model_dump(mode="json")


def _risk_summary(record: ForecastRecord) -> dict[str, object]:
    forecast = record.forecast
    return {
        "hours_to_stockout": forecast.hours_to_stockout,
        "stockout_probability_24h": forecast.stockout_probability_24h,
        "risk_level": forecast.risk_level.value,
        "p10_hours": forecast.p10_hours,
        "p50_hours": forecast.p50_hours,
        "p90_hours": forecast.p90_hours,
    }
