"""Pure domain logic for theoretical failure boundaries and constraint analysis.

Calculates theoretical days of cover from physical inventories and demand rates,
identifies which physical constraint binds under stressed operational conditions,
and computes service-level threshold crossover points from empirical sweeps.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def compute_theoretical_days_of_cover(
    depot_inventory: float | Mapping[str, float],
    scheduled_arrivals_liters: float | Mapping[str, float] = 0.0,
    daily_demand_liters: float | Mapping[str, float] = 91400.0,
) -> float:
    """Calculate theoretical days of fuel cover for the network or per-fuel breakdown.

    If inputs are mappings (by fuel type), returns the minimum cover across fuels.
    If scalar, computes (depot_inventory + arrivals) / daily_demand.
    """
    if isinstance(depot_inventory, Mapping) and isinstance(daily_demand_liters, Mapping):
        min_cover = float("inf")
        arr_map = (
            scheduled_arrivals_liters if isinstance(scheduled_arrivals_liters, Mapping) else {}
        )
        for fuel, dem in daily_demand_liters.items():
            if dem <= 0.0:
                continue
            inv = float(depot_inventory.get(fuel, 0.0))
            arr = float(arr_map.get(fuel, 0.0))
            cover = (inv + arr) / dem
            if cover < min_cover:
                min_cover = cover
        return min_cover

    # Scalar computation
    stock = (
        float(sum(depot_inventory.values()))
        if isinstance(depot_inventory, Mapping)
        else float(depot_inventory)
    )
    arr = (
        float(sum(scheduled_arrivals_liters.values()))
        if isinstance(scheduled_arrivals_liters, Mapping)
        else float(scheduled_arrivals_liters)
    )
    dem = (
        float(sum(daily_demand_liters.values()))
        if isinstance(daily_demand_liters, Mapping)
        else float(daily_demand_liters)
    )

    if dem <= 0.0:
        return float("inf")

    return (stock + arr) / dem


def identify_binding_constraint(
    depot_stock: float,
    route_max_shipment: float,
    station_ullage: float,
    transit_ticks: int,
    ticks_to_stockout: float,
    tick_consumption: float,
    needed_liters: float | None = None,
) -> str:
    """Identify which physical constraint binds first for an at-risk station.

    Order of physical evaluation:
    1. TRANSIT_DELAY_DEFICIT: fuel cannot arrive before the station runs dry.
    2. DEPOT_STOCK_EXHAUSTION: depot lacks physical inventory to supply the need.
    3. ROUTE_MAX_SHIPMENT: route max truck shipment cannot keep up with consumption rate.
    4. STATION_ULLAGE_HEADROOM: station tank headroom is smaller than needed replenishment.
    5. UNCONSTRAINED: all physical constraints satisfied.
    """
    effective_needed = (
        needed_liters
        if needed_liters is not None
        else min(route_max_shipment, max(tick_consumption * 4.0, 1000.0))
    )

    # 1. Transit delay deficit
    if ticks_to_stockout < float(transit_ticks):
        return "TRANSIT_DELAY_DEFICIT"

    # 2. Depot stock exhaustion
    if depot_stock < effective_needed or depot_stock < tick_consumption:
        return "DEPOT_STOCK_EXHAUSTION"

    # 3. Route max shipment throughput limit
    # If consumption over transit cycle exceeds max truck shipment
    if tick_consumption * max(1, transit_ticks) > route_max_shipment:
        return "ROUTE_MAX_SHIPMENT"

    # 4. Station ullage headroom
    if station_ullage < effective_needed:
        return "STATION_ULLAGE_HEADROOM"

    return "UNCONSTRAINED"


def find_service_level_thresholds(
    sweep_results: list[dict[str, Any]],
    x_key: str = "multiplier",
    service_level_key: str = "service_level",
) -> dict[str, float | None]:
    """Find the interpolated x-value where service level drops below 0.99, 0.95, and 0.90.

    Assumes sweep_results is sorted by x_key.
    """
    thresholds: dict[str, float | None] = {"p99": None, "p95": None, "p90": None}
    targets = [("p99", 0.99), ("p95", 0.95), ("p90", 0.90)]

    if len(sweep_results) < 2:
        return thresholds

    for label, target in targets:
        for i in range(len(sweep_results) - 1):
            r1 = sweep_results[i]
            r2 = sweep_results[i + 1]
            y1 = float(r1[service_level_key])
            y2 = float(r2[service_level_key])
            x1 = float(r1[x_key])
            x2 = float(r2[x_key])

            # Check if target is between y1 and y2 (monotonically decreasing)
            if y1 >= target >= y2 and y1 != y2:
                # Linear interpolation: x = x1 + (target - y1) * (x2 - x1) / (y2 - y1)
                x_cross = x1 + (target - y1) * (x2 - x1) / (y2 - y1)
                thresholds[label] = round(x_cross, 4)
                break
            elif y1 < target and thresholds[label] is None:
                # Crossed before or at start
                thresholds[label] = round(x1, 4)
                break

    return thresholds
