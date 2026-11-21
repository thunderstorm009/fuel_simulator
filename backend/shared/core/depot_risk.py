"""Pure depot and network-level supply risk projection.

Calculates depot cover, inventory runway, scheduled arrivals, committed allocations,
and 24-hour demand requirements for all fuel types across network depots.
Pure functions: zero I/O, deterministic, testable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.forecast import expected_demand
from core.models import AllocationStatus, FuelType, Snapshot, SupplyArrivalStatus


@dataclass(frozen=True)
class DepotRiskProjection:
    depot_id: str
    depot_name: str
    fuel_type: str
    current_inventory: float
    scheduled_arrivals: float
    committed_allocations: float
    projected_demand: float
    net_cover_liters: float
    cover_hours: float
    is_bottleneck: bool
    dispatch_utilization: float
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_depot_risks(
    snapshot: Snapshot, horizon_hours: float = 24.0
) -> list[DepotRiskProjection]:
    """Calculate forward supply cover and bottleneck risk per depot and fuel type.

    Formula:
    Net cover = current_inventory + scheduled_arrivals - committed_allocations - projected_demand.

    - current_inventory: on-hand physical stock at the depot.
    - scheduled_arrivals: arrivals arriving within horizon (<= tick + horizon_ticks).
    - committed_allocations: active outbound allocations (PENDING or IN_TRANSIT) from this depot.
    - projected_demand: projected demand over horizon across stations reachable from this depot.
    - cover_hours: hours until stock depletion at projected burn rate.
    - is_bottleneck: True if net_cover_liters < 0 or dispatch_utilization >= 0.80.
    """
    projections: list[DepotRiskProjection] = []
    tick_minutes = max(1, snapshot.instance.tick_minutes)
    horizon_ticks = max(1, round(horizon_hours * 60.0 / tick_minutes))
    current_tick = snapshot.instance.tick
    cutoff_tick = current_tick + horizon_ticks

    # Pre-index routes by depot
    routes_by_depot: dict[str, list[str]] = {}
    for r in snapshot.routes:
        routes_by_depot.setdefault(r.source_depot_id, []).append(r.destination_station_id)

    # Station lookup
    station_map = {s.id: s for s in snapshot.stations}

    for depot in snapshot.depots:
        # Calculate active outbound allocations for this depot
        active_allocations = [
            a
            for a in snapshot.allocations
            if a.source_depot_id == depot.id
            and a.status in {AllocationStatus.PENDING, AllocationStatus.IN_TRANSIT}
        ]

        # Dispatch utilization for tick
        tick_dispatches = sum(
            a.quantity
            for a in active_allocations
            if getattr(a, "created_tick", current_tick) == current_tick
        )
        dispatch_utilization = tick_dispatches / max(1.0, depot.dispatch_capacity_per_tick)

        # Reachable stations from this depot
        reachable_station_ids = set(routes_by_depot.get(depot.id, []))
        reachable_stations = [
            station_map[sid] for sid in reachable_station_ids if sid in station_map
        ]

        for fuel in (FuelType.DIESEL, FuelType.PETROL, FuelType.OCTANE):
            depot_stock = float(depot.inventory.get(fuel, 0.0))

            # Scheduled arrivals within horizon
            arrivals_in_horizon = [
                a
                for a in snapshot.supply_arrivals
                if a.depot_id == depot.id
                and a.fuel_type is fuel
                and a.status in {SupplyArrivalStatus.SCHEDULED, SupplyArrivalStatus.DELAYED}
                and a.planned_tick <= cutoff_tick
                and (a.actual_tick is None or a.actual_tick > current_tick)
            ]
            scheduled_arrivals = sum(float(a.quantity) for a in arrivals_in_horizon)

            # Committed allocations of this fuel type
            committed = sum(float(a.quantity) for a in active_allocations if a.fuel_type is fuel)

            # Projected 24h demand of served stations
            projected_demand = 0.0
            for station in reachable_stations:
                rates = [
                    expected_demand(
                        station.demand_profile,
                        fuel.value,
                        snapshot.instance.sim_time,
                        station.demand_multiplier,
                        tick_minutes,
                    )
                    for _ in range(horizon_ticks)
                ]
                projected_demand += sum(rates)

            net_cover = depot_stock + scheduled_arrivals - committed - projected_demand

            # Hourly burn rate
            hourly_burn = projected_demand / max(0.1, horizon_hours)
            available_supply = max(0.0, depot_stock + scheduled_arrivals - committed)
            if hourly_burn > 0:
                cover_hours = round(available_supply / hourly_burn, 1)
            else:
                cover_hours = 999.0

            is_bottleneck = net_cover < 0 or dispatch_utilization >= 0.80

            projections.append(
                DepotRiskProjection(
                    depot_id=depot.id,
                    depot_name=depot.name,
                    fuel_type=fuel.value,
                    current_inventory=round(depot_stock, 1),
                    scheduled_arrivals=round(scheduled_arrivals, 1),
                    committed_allocations=round(committed, 1),
                    projected_demand=round(projected_demand, 1),
                    net_cover_liters=round(net_cover, 1),
                    cover_hours=cover_hours,
                    is_bottleneck=is_bottleneck,
                    dispatch_utilization=round(dispatch_utilization, 3),
                    evidence={
                        "depot_id": depot.id,
                        "fuel_type": fuel.value,
                        "horizon_hours": horizon_hours,
                        "arrivals_count": len(arrivals_in_horizon),
                        "reachable_stations_count": len(reachable_stations),
                        "dispatch_capacity": depot.dispatch_capacity_per_tick,
                    },
                )
            )

    return projections
