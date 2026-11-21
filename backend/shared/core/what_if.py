"""Pure what-if allocation simulation without simulator I/O or state modification."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.depot_risk import calculate_depot_risks
from core.models import Allocation, AllocationStatus, AllocationTerms, FuelType, Snapshot
from core.risk import forecast_pair
from core.validator import validate


class WhatIfCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_depot_id: str
    destination_station_id: str
    route_id: str
    fuel_type: FuelType
    quantity: float = Field(gt=0)


class WhatIfTrajectoryPoint(BaseModel):
    tick_offset: int
    mean_inventory: float
    p10_inventory: float
    p90_inventory: float


class WhatIfCondition(BaseModel):
    hours_to_stockout: Optional[float]
    stockout_probability_24h: float
    risk_level: str
    trajectory: list[WhatIfTrajectoryPoint]
    depot_net_cover_liters: float
    depot_cover_hours: float


class WhatIfDelta(BaseModel):
    hours_to_stockout_change: Optional[float]
    stockout_probability_change: float
    depot_net_cover_change: float


class WhatIfResult(BaseModel):
    feasible: bool
    violations: list[dict[str, str]]
    verdict: str  # 'FEASIBLE_BENEFICIAL', 'FEASIBLE_NEUTRAL', 'INFEASIBLE'
    before: WhatIfCondition
    after: WhatIfCondition
    delta: WhatIfDelta
    simulated: bool = True


def simulate_what_if(
    snapshot: Snapshot,
    candidate: WhatIfCandidate,
    seed: int = 42,
) -> WhatIfResult:
    """Evaluate constraint feasibility and calculate before/after trajectories and depot impacts."""
    station = next(
        (s for s in snapshot.stations if s.id == candidate.destination_station_id),
        None,
    )
    if station is None:
        raise ValueError(f"Station {candidate.destination_station_id} not found in snapshot")

    # 1. Constraint validation
    terms = AllocationTerms(
        source_depot_id=candidate.source_depot_id,
        destination_station_id=candidate.destination_station_id,
        route_id=candidate.route_id,
        fuel_type=candidate.fuel_type,
        quantity=candidate.quantity,
    )
    raw_violations = validate(terms, snapshot)
    feasible = len(raw_violations) == 0
    violations_formatted = [{"code": v.code, "message": v.message} for v in raw_violations]

    # 2. Baseline assessment (before shipment)
    pair_seed = (seed + snapshot.instance.tick * 9176) % 2**32
    before_record = forecast_pair(snapshot, station, candidate.fuel_type, seed=pair_seed)
    depot_risks_before = calculate_depot_risks(snapshot)
    depot_before = next(
        (
            r
            for r in depot_risks_before
            if r.depot_id == candidate.source_depot_id and r.fuel_type == candidate.fuel_type
        ),
        None,
    )
    depot_cover_liters_before = depot_before.net_cover_liters if depot_before else 0.0
    depot_cover_hours_before = depot_before.cover_hours if depot_before else 0.0

    # 3. Simulated state assessment (with hypothetical shipment in transit)
    sim_snapshot = snapshot.model_copy(deep=True)
    route = next((r for r in snapshot.routes if r.id == candidate.route_id), None)
    transit_ticks = route.transit_ticks if route else 4
    arrival_tick = snapshot.instance.tick + 1 + transit_ticks

    new_alloc_id = max((a.id for a in sim_snapshot.allocations), default=0) + 1
    sim_snapshot.allocations.append(
        Allocation(
            id=new_alloc_id,
            idempotency_key="what-if-temp",
            source_depot_id=candidate.source_depot_id,
            destination_station_id=candidate.destination_station_id,
            route_id=candidate.route_id,
            fuel_type=candidate.fuel_type,
            quantity=candidate.quantity,
            created_tick=snapshot.instance.tick,
            departure_tick=snapshot.instance.tick + 1,
            expected_arrival_tick=arrival_tick,
            actual_arrival_tick=None,
            status=AllocationStatus.IN_TRANSIT,
            failure_reason=None,
        )
    )

    sim_station = next(s for s in sim_snapshot.stations if s.id == candidate.destination_station_id)
    after_record = forecast_pair(sim_snapshot, sim_station, candidate.fuel_type, seed=pair_seed)
    depot_risks_after = calculate_depot_risks(sim_snapshot)
    depot_after = next(
        (
            r
            for r in depot_risks_after
            if r.depot_id == candidate.source_depot_id and r.fuel_type == candidate.fuel_type
        ),
        None,
    )
    depot_cover_liters_after = depot_after.net_cover_liters if depot_after else 0.0
    depot_cover_hours_after = depot_after.cover_hours if depot_after else 0.0

    # 4. Deltas and Verdict
    h_before = before_record.forecast.hours_to_stockout
    h_after = after_record.forecast.hours_to_stockout
    if h_after is not None and h_before is not None:
        delta_hours: Optional[float] = round(h_after - h_before, 2)
    elif h_before is None and h_after is not None:
        delta_hours = 0.0
    elif h_before is not None and h_after is None:
        delta_hours = round(24.0 - h_before, 2)
    else:
        delta_hours = 0.0

    delta_prob = round(
        after_record.forecast.stockout_probability_24h
        - before_record.forecast.stockout_probability_24h,
        3,
    )
    delta_cover = round(depot_cover_liters_after - depot_cover_liters_before, 1)

    if not feasible:
        verdict = "INFEASIBLE"
    elif (delta_hours is not None and delta_hours > 0.0) or delta_prob < -0.02:
        verdict = "FEASIBLE_BENEFICIAL"
    else:
        verdict = "FEASIBLE_NEUTRAL"

    before_condition = WhatIfCondition(
        hours_to_stockout=h_before,
        stockout_probability_24h=before_record.forecast.stockout_probability_24h,
        risk_level=before_record.forecast.risk_level.value,
        trajectory=[
            WhatIfTrajectoryPoint(
                tick_offset=p.tick_offset,
                mean_inventory=p.mean_inventory,
                p10_inventory=p.p10_inventory,
                p90_inventory=p.p90_inventory,
            )
            for p in before_record.trajectory
        ],
        depot_net_cover_liters=round(depot_cover_liters_before, 1),
        depot_cover_hours=round(depot_cover_hours_before, 1),
    )

    after_condition = WhatIfCondition(
        hours_to_stockout=h_after,
        stockout_probability_24h=after_record.forecast.stockout_probability_24h,
        risk_level=after_record.forecast.risk_level.value,
        trajectory=[
            WhatIfTrajectoryPoint(
                tick_offset=p.tick_offset,
                mean_inventory=p.mean_inventory,
                p10_inventory=p.p10_inventory,
                p90_inventory=p.p90_inventory,
            )
            for p in after_record.trajectory
        ],
        depot_net_cover_liters=round(depot_cover_liters_after, 1),
        depot_cover_hours=round(depot_cover_hours_after, 1),
    )

    return WhatIfResult(
        feasible=feasible,
        violations=violations_formatted,
        verdict=verdict,
        before=before_condition,
        after=after_condition,
        delta=WhatIfDelta(
            hours_to_stockout_change=delta_hours,
            stockout_probability_change=delta_prob,
            depot_net_cover_change=delta_cover,
        ),
        simulated=True,
    )
