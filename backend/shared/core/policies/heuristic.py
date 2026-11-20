"""Urgency-first, constraint-validated allocation heuristic."""

from __future__ import annotations

from collections.abc import Sequence

from core.forecast import future_demand_rates
from core.models import (
    AllocationRequest,
    AllocationStatus,
    AllocationTerms,
    FuelType,
    Snapshot,
)
from core.policies.base import PolicyPlan
from core.risk import ForecastRecord
from core.validator import validate


class HeuristicPolicy:
    name = "heuristic"

    def recommend(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> list[PolicyPlan]:
        records = sorted(
            forecasts,
            key=lambda row: (
                row.forecast.hours_to_stockout
                if row.forecast.hours_to_stockout is not None
                else 24.0,
                row.forecast.station_id,
                row.forecast.fuel_type.value,
            ),
        )
        plans: list[PolicyPlan] = []
        reservations: list[AllocationTerms] = []
        for record in records:
            forecast = record.forecast
            if not self._at_risk(record):
                continue
            station = next(
                (row for row in snapshot.stations if row.id == forecast.station_id), None
            )
            if station is None:
                continue
            fuel = forecast.fuel_type
            if self._already_allocated(snapshot, station.id, fuel):
                continue
            multiplier = float(record.drivers.get("demand_multiplier", station.demand_multiplier))
            recent_ratio = float(record.drivers.get("recent_ratio", 1.0))
            rates = future_demand_rates(
                station.demand_profile,
                fuel,
                snapshot.instance.sim_time,
                multiplier,
                recent_ratio,
                snapshot.instance.tick_minutes,
            )
            target_inventory = min(station.capacity[fuel] * 0.7, sum(rates))
            free_capacity = station.capacity[fuel] - station.inventory[fuel]
            if free_capacity <= 0:
                continue
            routes = [
                route for route in snapshot.routes if route.destination_station_id == station.id
            ]
            route_candidates = sorted(
                routes,
                key=lambda route: (
                    not self._arrives_before_stockout(
                        route.transit_ticks,
                        forecast.hours_to_stockout,
                        snapshot.instance.tick_minutes,
                    ),
                    route.transit_ticks,
                    route.id,
                ),
            )
            need_remaining = max(0.0, target_inventory - station.inventory[fuel])
            rejected: list[dict[str, object]] = []
            for route in route_candidates:
                if need_remaining <= 0 or free_capacity <= 0:
                    break
                depot = next(
                    (row for row in snapshot.depots if row.id == route.source_depot_id), None
                )
                if depot is None:
                    continue
                stock_at_arrival = self._projected_inventory(record, route.transit_ticks)
                need_at_arrival = max(0.0, target_inventory - stock_at_arrival)
                quantity_remaining = min(need_remaining, need_at_arrival, free_capacity)
                while quantity_remaining > 1e-6:
                    reserved_from_depot = sum(
                        item.quantity
                        for item in reservations
                        if item.source_depot_id == depot.id and item.fuel_type is fuel
                    )
                    reserved_dispatch = sum(
                        item.quantity for item in reservations if item.source_depot_id == depot.id
                    )
                    current_dispatch = sum(
                        allocation.quantity
                        for allocation in snapshot.allocations
                        if allocation.source_depot_id == depot.id
                        and allocation.created_tick == snapshot.instance.tick
                        and allocation.status
                        in {AllocationStatus.PENDING, AllocationStatus.IN_TRANSIT}
                    )
                    reserved_destination = sum(
                        item.quantity
                        for item in reservations
                        if item.destination_station_id == station.id and item.fuel_type is fuel
                    )
                    dispatch_remaining = (
                        depot.dispatch_capacity_per_tick - current_dispatch - reserved_dispatch
                    )
                    depot_remaining = depot.inventory[fuel] - reserved_from_depot
                    capacity_remaining = (
                        station.capacity[fuel] - station.inventory[fuel] - reserved_destination
                    )
                    quantity = min(
                        quantity_remaining,
                        route.max_shipment,
                        depot_remaining,
                        dispatch_remaining,
                        capacity_remaining,
                    )
                    if quantity <= 1e-6:
                        if depot.status.value not in {"OPEN", "CONSTRAINED"}:
                            rejected.append({"route_id": route.id, "reason": "DEPOT_CLOSED"})
                        elif route.status.value != "AVAILABLE":
                            rejected.append({"route_id": route.id, "reason": "ROUTE_DISRUPTED"})
                        elif depot_remaining <= 1e-6:
                            rejected.append(
                                {"route_id": route.id, "reason": "INSUFFICIENT_INVENTORY"}
                            )
                        elif dispatch_remaining <= 1e-6:
                            rejected.append(
                                {"route_id": route.id, "reason": "DISPATCH_CAPACITY_EXCEEDED"}
                            )
                        else:
                            rejected.append(
                                {"route_id": route.id, "reason": "NO_REMAINING_CAPACITY"}
                            )
                        break
                    terms = AllocationTerms(
                        source_depot_id=depot.id,
                        destination_station_id=station.id,
                        route_id=route.id,
                        fuel_type=fuel,
                        quantity=quantity,
                    )
                    validation_request = AllocationRequest(
                        idempotency_key="validation-only", **terms.model_dump()
                    )
                    violations = validate(validation_request, snapshot, reservations)
                    if violations:
                        rejected.append({"route_id": route.id, "reason": violations[0].code})
                        break
                    # A newly submitted allocation departs on the current simulator tick.
                    arrival_tick = snapshot.instance.tick + route.transit_ticks
                    constraints = [
                        {"constraint": "max_shipment", "limit_liters": route.max_shipment},
                        {
                            "constraint": "depot_inventory",
                            "available_liters": depot_remaining,
                        },
                        {
                            "constraint": "dispatch_capacity",
                            "available_liters": dispatch_remaining,
                        },
                        {
                            "constraint": "destination_capacity",
                            "available_liters": capacity_remaining,
                        },
                    ]
                    plans.append(
                        PolicyPlan(
                            request=terms,
                            stockout_hours=forecast.hours_to_stockout,
                            arrival_tick=arrival_tick,
                            projected_inventory_at_arrival=stock_at_arrival,
                            target_inventory=target_inventory,
                            constraints_applied=constraints,
                            alternatives=rejected.copy(),
                        )
                    )
                    reservations.append(terms)
                    need_remaining -= quantity
                    quantity_remaining -= quantity
                    free_capacity -= quantity
                    reserved_destination += quantity
                    if quantity_remaining <= 1e-6:
                        break
            if rejected:
                for plan in plans:
                    if plan.request.destination_station_id == station.id:
                        plan.alternatives.extend(rejected)
        return plans

    @staticmethod
    def _at_risk(record: ForecastRecord) -> bool:
        hours = record.forecast.hours_to_stockout
        return (hours is not None and hours < 24) or record.forecast.stockout_probability_24h >= 0.5

    @staticmethod
    def _already_allocated(snapshot: Snapshot, station_id: str, fuel: FuelType) -> bool:
        return any(
            allocation.destination_station_id == station_id
            and allocation.fuel_type is fuel
            and allocation.status in {AllocationStatus.PENDING, AllocationStatus.IN_TRANSIT}
            for allocation in snapshot.allocations
        )

    @staticmethod
    def _arrives_before_stockout(
        arrival_offset: int, hours: float | None, tick_minutes: int
    ) -> bool:
        return hours is not None and arrival_offset * tick_minutes / 60 < hours

    @staticmethod
    def _projected_inventory(record: ForecastRecord, arrival_offset: int) -> float:
        index = min(max(0, arrival_offset), len(record.trajectory) - 1)
        return record.trajectory[index].mean_inventory
