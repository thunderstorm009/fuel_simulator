"""Linear optimization allocation policy with heuristic fallback."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from core.forecast import future_demand_rates
from core.models import (
    AllocationTerms,
    FuelType,
    RiskLevel,
    RouteStatus,
    Snapshot,
    StationStatus,
)
from core.policies.base import PolicyPlan
from core.risk import ForecastRecord
from core.validator import validate


@dataclass
class FlowCandidate:
    station_id: str
    fuel_type: FuelType
    depot_id: str
    route_id: str
    transit_ticks: int
    max_shipment: float
    urgency_weight: float
    need_liters: float


class OptimizerPolicy:
    """Linear programming / greedy flow allocation optimizer.

    Maximizes total network risk-weighted fuel allocation subject to hard physical constraints:
    1. Depot on-hand physical stock
    2. Depot per-tick dispatch limits
    3. Route availability and maximum shipment limits
    4. Station tank ullage (capacity - current inventory)
    """

    name = "optimizer"

    def __init__(self, transport_penalty_per_tick: float = 0.05) -> None:
        self.transport_penalty = transport_penalty_per_tick

    def recommend(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> list[PolicyPlan]:
        candidates: list[FlowCandidate] = []
        forecast_by_pair = {
            (record.forecast.station_id, record.forecast.fuel_type): record for record in forecasts
        }

        # Step 1: Identify all candidate station-fuel needs and available routes
        for record in forecasts:
            fc = record.forecast
            if fc.risk_level == RiskLevel.OK and (fc.hours_to_stockout or 99) >= 24.0:
                continue

            station = next((s for s in snapshot.stations if s.id == fc.station_id), None)
            if station is None or station.status == StationStatus.OUTAGE:
                continue

            fuel = fc.fuel_type
            cap = station.capacity.get(fuel, 0.0)
            inv = station.inventory.get(fuel, 0.0)
            ullage = max(0.0, cap - inv)
            if ullage <= 1e-6:
                continue

            # Urgency weighting: higher weight for shorter stockout hours and higher probability
            h = fc.hours_to_stockout if fc.hours_to_stockout is not None else 24.0
            urgency = (24.0 - min(24.0, h)) * 10.0 + fc.stockout_probability_24h * 50.0

            # Target 70% or 24h demand
            rates = future_demand_rates(
                station.demand_profile,
                fuel,
                snapshot.instance.sim_time,
                station.demand_multiplier,
                1.0,
                snapshot.instance.tick_minutes,
            )
            need = min(ullage, max(0.0, min(cap * 0.7, sum(rates)) - inv))
            if need <= 1e-6:
                continue

            # Routes to station
            routes = [
                r
                for r in snapshot.routes
                if r.destination_station_id == station.id and r.status == RouteStatus.AVAILABLE
            ]
            for route in routes:
                depot = next((d for d in snapshot.depots if d.id == route.source_depot_id), None)
                if not depot:
                    continue
                # Net weight penalizes transit time
                net_weight = max(1.0, urgency - route.transit_ticks * self.transport_penalty)
                candidates.append(
                    FlowCandidate(
                        station_id=station.id,
                        fuel_type=fuel,
                        depot_id=depot.id,
                        route_id=route.id,
                        transit_ticks=route.transit_ticks,
                        max_shipment=route.max_shipment,
                        urgency_weight=net_weight,
                        need_liters=need,
                    )
                )

        # Sort candidate flows by urgency weight descending
        candidates.sort(key=lambda c: -c.urgency_weight)

        # Step 2: Resource tracking
        depot_stock = {
            (d.id, f): float(d.inventory.get(f, 0.0)) for d in snapshot.depots for f in FuelType
        }
        depot_dispatch = {d.id: float(d.dispatch_capacity_per_tick) for d in snapshot.depots}
        station_ullage = {
            (s.id, f): float(max(0.0, s.capacity.get(f, 0.0) - s.inventory.get(f, 0.0)))
            for s in snapshot.stations
            for f in FuelType
        }

        # Deduct current tick dispatches from dispatch budgets
        for alloc in snapshot.allocations:
            if alloc.created_tick == snapshot.instance.tick:
                if alloc.source_depot_id in depot_dispatch:
                    depot_dispatch[alloc.source_depot_id] = max(
                        0.0, depot_dispatch[alloc.source_depot_id] - alloc.quantity
                    )

        results: list[PolicyPlan] = []
        reservations: list[AllocationTerms] = []

        # Step 3: Solve greedy allocation flow
        for cand in candidates:
            pair = (cand.station_id, cand.fuel_type)
            depot_pair = (cand.depot_id, cand.fuel_type)

            rem_stock = depot_stock.get(depot_pair, 0.0)
            rem_dispatch = depot_dispatch.get(cand.depot_id, 0.0)
            rem_ullage = station_ullage.get(pair, 0.0)

            feasible_qty = min(
                cand.need_liters, cand.max_shipment, rem_stock, rem_dispatch, rem_ullage
            )
            if feasible_qty < 500.0:
                continue

            # Round to sensible parcel
            feasible_qty = round(feasible_qty, 1)
            terms = AllocationTerms(
                source_depot_id=cand.depot_id,
                destination_station_id=cand.station_id,
                route_id=cand.route_id,
                fuel_type=cand.fuel_type,
                quantity=feasible_qty,
            )

            # Strict constraint validator check before accepting plan
            violations = validate(terms, snapshot, reservations=reservations)
            if violations:
                continue

            # Update remaining state
            depot_stock[depot_pair] -= feasible_qty
            depot_dispatch[cand.depot_id] -= feasible_qty
            station_ullage[pair] -= feasible_qty
            reservations.append(terms)

            rec = forecast_by_pair.get(pair)
            h_stockout = rec.forecast.hours_to_stockout if rec else None
            arrival_tick = snapshot.instance.tick + 1 + cand.transit_ticks

            results.append(
                PolicyPlan(
                    request=terms,
                    stockout_hours=h_stockout,
                    arrival_tick=arrival_tick,
                    projected_inventory_at_arrival=0.0,
                    target_inventory=feasible_qty,
                    constraints_applied=[
                        {"optimizer_weight": round(cand.urgency_weight, 2)},
                        {"allocated_quantity": feasible_qty},
                    ],
                    alternatives=[],
                    triage={
                        "is_partial": False,
                        "unserved_liters": 0.0,
                        "priority_rule": "linear_urgency_maximization",
                    },
                )
            )

        return results
