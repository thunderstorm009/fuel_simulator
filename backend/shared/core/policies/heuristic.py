"""Urgency-first, constraint-validated allocation heuristic with two-pass triage."""

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
        candidates: list[dict[str, object]] = []
        for record in forecasts:
            forecast = record.forecast
            if not self._at_risk(record):
                continue
            station = next(
                (row for row in snapshot.stations if row.id == forecast.station_id), None
            )
            if station is None or getattr(station.status, "value", station.status) in {
                "OUTAGE",
                "CLOSED",
            }:
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
            if free_capacity <= 1e-6:
                continue

            # Need to reach 70% target
            need_full = max(0.0, target_inventory - station.inventory[fuel])
            if need_full <= 1e-6:
                continue

            # 12 simulated hours emergency demand threshold
            ticks_12h = max(1, round(12.0 * 60.0 / max(1, snapshot.instance.tick_minutes)))
            emergency_demand = sum(rates[: min(ticks_12h, len(rates))])
            need_emergency = min(need_full, max(0.0, emergency_demand - station.inventory[fuel]))

            candidates.append(
                {
                    "record": record,
                    "station": station,
                    "fuel": fuel,
                    "rates": rates,
                    "target_inventory": target_inventory,
                    "need_full": need_full,
                    "need_emergency": need_emergency,
                    "free_capacity": free_capacity,
                }
            )

        # Sort candidates by urgency: lowest hours to stockout first, then stockout probability
        candidates.sort(
            key=lambda c: (
                c["record"].forecast.hours_to_stockout
                if c["record"].forecast.hours_to_stockout is not None
                else 24.0,
                -c["record"].forecast.stockout_probability_24h,
                c["station"].id,
                c["fuel"].value,
            )
        )

        reservations: list[AllocationTerms] = []
        allocated_by_cand: list[float] = [0.0] * len(candidates)
        plans_raw: list[list[dict[str, object]]] = [[] for _ in candidates]
        rejections_by_cand: list[list[dict[str, object]]] = [[] for _ in candidates]

        # Sort routes: arrives in time first, OPEN depot before CONSTRAINED, shortest transit
        def sort_routes(routes: list, forecast: ForecastRecord) -> list:
            def key_fn(r):
                depot = next((d for d in snapshot.depots if d.id == r.source_depot_id), None)
                is_constrained = (
                    1
                    if (depot and getattr(depot.status, "value", depot.status) == "CONSTRAINED")
                    else 0
                )
                arrives_in_time = (
                    0
                    if self._arrives_before_stockout(
                        r.transit_ticks,
                        forecast.forecast.hours_to_stockout,
                        snapshot.instance.tick_minutes,
                    )
                    else 1
                )
                return (arrives_in_time, is_constrained, r.transit_ticks, r.id)

            return sorted(routes, key=key_fn)

        # Allocation step function for a given quantity target
        def try_allocate(cand_idx: int, target_amount: float) -> float:
            c = candidates[cand_idx]
            station = c["station"]
            fuel = c["fuel"]
            record = c["record"]
            all_routes = [r for r in snapshot.routes if r.destination_station_id == station.id]
            sorted_routes = sort_routes(all_routes, record)

            need_remaining = target_amount
            allocated_here = 0.0

            for route in sorted_routes:
                if need_remaining <= 1e-6:
                    break
                depot = next((d for d in snapshot.depots if d.id == route.source_depot_id), None)
                if depot is None:
                    continue

                stock_at_arrival = self._projected_inventory(record, route.transit_ticks)
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
                    and allocation.status in {AllocationStatus.PENDING, AllocationStatus.IN_TRANSIT}
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
                    need_remaining,
                    route.max_shipment,
                    depot_remaining,
                    dispatch_remaining,
                    capacity_remaining,
                )

                if quantity <= 1e-6:
                    if getattr(depot.status, "value", depot.status) not in {
                        "OPEN",
                        "CONSTRAINED",
                    }:
                        rejections_by_cand[cand_idx].append(
                            {"route_id": route.id, "reason": "DEPOT_CLOSED"}
                        )
                    elif getattr(route.status, "value", route.status) != "AVAILABLE":
                        rejections_by_cand[cand_idx].append(
                            {"route_id": route.id, "reason": "ROUTE_DISRUPTED"}
                        )
                    elif depot_remaining <= 1e-6:
                        rejections_by_cand[cand_idx].append(
                            {
                                "route_id": route.id,
                                "reason": f"INSUFFICIENT_DEPOT_INVENTORY:{depot.id}",
                            }
                        )
                    elif dispatch_remaining <= 1e-6:
                        rejections_by_cand[cand_idx].append(
                            {
                                "route_id": route.id,
                                "reason": f"DISPATCH_CAPACITY_EXCEEDED:{depot.id}",
                            }
                        )
                    else:
                        rejections_by_cand[cand_idx].append(
                            {"route_id": route.id, "reason": "DESTINATION_CAPACITY_EXCEEDED"}
                        )
                    continue

                terms = AllocationTerms(
                    source_depot_id=depot.id,
                    destination_station_id=station.id,
                    route_id=route.id,
                    fuel_type=fuel,
                    quantity=quantity,
                )
                val_req = AllocationRequest(idempotency_key="validation-only", **terms.model_dump())
                violations = validate(val_req, snapshot, reservations)
                if violations:
                    rejections_by_cand[cand_idx].append(
                        {"route_id": route.id, "reason": violations[0].code}
                    )
                    continue

                constraints = [
                    {"constraint": "max_shipment", "limit_liters": route.max_shipment},
                    {"constraint": "depot_inventory", "available_liters": depot_remaining},
                    {"constraint": "dispatch_capacity", "available_liters": dispatch_remaining},
                    {"constraint": "destination_capacity", "available_liters": capacity_remaining},
                ]
                if getattr(depot.status, "value", depot.status) == "CONSTRAINED":
                    constraints.append(
                        {
                            "constraint": "depot_constrained",
                            "note": (f"Depot {depot.id} is CONSTRAINED; utilized as best option"),
                        }
                    )

                plans_raw[cand_idx].append(
                    {
                        "terms": terms,
                        "arrival_tick": snapshot.instance.tick + route.transit_ticks,
                        "stock_at_arrival": stock_at_arrival,
                        "constraints": constraints,
                    }
                )
                reservations.append(terms)
                allocated_here += quantity
                need_remaining -= quantity

            return allocated_here

        # PASS 1: Emergency 12h stockout removal
        for idx, c in enumerate(candidates):
            emerg_need = c["need_emergency"]
            if emerg_need > 1e-6:
                alloc = try_allocate(idx, emerg_need)
                allocated_by_cand[idx] += alloc

        # PASS 2: Top-up toward target inventory
        for idx, c in enumerate(candidates):
            rem_need = c["need_full"] - allocated_by_cand[idx]
            if rem_need > 1e-6:
                alloc = try_allocate(idx, rem_need)
                allocated_by_cand[idx] += alloc

        # Assemble final PolicyPlans with structured triage details
        results: list[PolicyPlan] = []
        for idx, c in enumerate(candidates):
            tot_allocated = allocated_by_cand[idx]
            record = c["record"]
            target_inv = c["target_inventory"]
            need_full = c["need_full"]
            is_partial = tot_allocated < (need_full - 1e-6)

            unserved_reason = None
            if is_partial:
                if rejections_by_cand[idx]:
                    unserved_reason = rejections_by_cand[idx][-1]["reason"]
                else:
                    unserved_reason = "SUPPLY_CONSTRAINED_AT_DEPOT"

            triage_info = {
                "is_partial": is_partial,
                "unserved_liters": round(max(0.0, need_full - tot_allocated), 2),
                "unserved_reason": unserved_reason,
                "priority_rule": "two_pass_urgency_12h_then_target",
                "requested_full": round(need_full, 2),
                "allocated": round(tot_allocated, 2),
            }

            consolidated: list[dict[str, object]] = []
            for item in plans_raw[idx]:
                terms = item["terms"]
                route = next((r for r in snapshot.routes if r.id == terms.route_id), None)
                max_ship = route.max_shipment if route else 7000.0
                existing = next(
                    (
                        x
                        for x in consolidated
                        if x["terms"].route_id == terms.route_id
                        and x["terms"].quantity + terms.quantity <= max_ship + 1e-6
                    ),
                    None,
                )
                if existing:
                    prev_terms = existing["terms"]
                    existing["terms"] = AllocationTerms(
                        source_depot_id=prev_terms.source_depot_id,
                        destination_station_id=prev_terms.destination_station_id,
                        route_id=prev_terms.route_id,
                        fuel_type=prev_terms.fuel_type,
                        quantity=prev_terms.quantity + terms.quantity,
                    )
                else:
                    consolidated.append(dict(item))

            for item in consolidated:
                results.append(
                    PolicyPlan(
                        request=item["terms"],
                        stockout_hours=record.forecast.hours_to_stockout,
                        arrival_tick=item["arrival_tick"],
                        projected_inventory_at_arrival=item["stock_at_arrival"],
                        target_inventory=target_inv,
                        constraints_applied=item["constraints"],
                        alternatives=rejections_by_cand[idx].copy(),
                        triage=triage_info,
                    )
                )

        return results

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
        if not record.trajectory:
            return 0.0
        index = min(max(0, arrival_offset), len(record.trajectory) - 1)
        return record.trajectory[index].mean_inventory
