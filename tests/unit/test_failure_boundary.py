"""Unit tests for failure boundary calculations and constraint binding classification."""

from core.failure_boundary import (
    compute_theoretical_days_of_cover,
    find_service_level_thresholds,
    identify_binding_constraint,
)


def test_compute_theoretical_days_of_cover_scalar():
    # 252,000 L depot stock, 0 scheduled arrivals, 91,400 L/day demand
    # Cover = 252000 / 91400 = ~2.757 days
    cover = compute_theoretical_days_of_cover(252000.0, 0.0, 91400.0)
    assert abs(cover - 2.7571) < 0.001


def test_compute_theoretical_days_of_cover_with_arrivals():
    # 252,000 L stock + 91,400 L arrivals, 91,400 L/day demand
    # Cover = (252000 + 91400) / 91400 = ~3.757 days
    cover = compute_theoretical_days_of_cover(252000.0, 91400.0, 91400.0)
    assert abs(cover - 3.7571) < 0.001


def test_compute_theoretical_days_of_cover_zero_demand():
    cover = compute_theoretical_days_of_cover(100000.0, 0.0, 0.0)
    assert cover == float("inf")


def test_compute_theoretical_days_of_cover_by_fuel():
    depot_inv = {"DIESEL": 115000.0, "PETROL": 87000.0, "OCTANE": 50000.0}
    daily_demand = {"DIESEL": 40200.0, "PETROL": 33600.0, "OCTANE": 17600.0}
    # DIESEL: 115000 / 40200 = 2.86 days
    # PETROL: 87000 / 33600 = 2.589 days
    # OCTANE: 50000 / 17600 = 2.84 days
    # Min cover is PETROL ~2.589 days
    res = compute_theoretical_days_of_cover(depot_inv, 0.0, daily_demand)
    assert abs(res - 2.589) < 0.01


def test_identify_binding_constraint_depot_exhaustion():
    binding = identify_binding_constraint(
        depot_stock=500.0,
        route_max_shipment=6000.0,
        station_ullage=20000.0,
        transit_ticks=2,
        ticks_to_stockout=10.0,
        tick_consumption=800.0,
    )
    assert binding == "DEPOT_STOCK_EXHAUSTION"


def test_identify_binding_constraint_transit_delay():
    binding = identify_binding_constraint(
        depot_stock=50000.0,
        route_max_shipment=6000.0,
        station_ullage=20000.0,
        transit_ticks=4,
        ticks_to_stockout=2.0,  # will stock out before transit arrives
        tick_consumption=800.0,
    )
    assert binding == "TRANSIT_DELAY_DEFICIT"


def test_identify_binding_constraint_route_max():
    # If consumption per tick is 3500 L and route cap is 5000 L with 2 ticks transit
    # Maximum throughput is 2500 L/tick
    binding = identify_binding_constraint(
        depot_stock=50000.0,
        route_max_shipment=5000.0,
        station_ullage=20000.0,
        transit_ticks=2,
        ticks_to_stockout=10.0,
        tick_consumption=3500.0,
    )
    assert binding == "ROUTE_MAX_SHIPMENT"


def test_identify_binding_constraint_station_ullage():
    # Needed delivery is 5000 L, but station tank headroom is only 500 L
    binding = identify_binding_constraint(
        depot_stock=50000.0,
        route_max_shipment=6000.0,
        station_ullage=500.0,
        transit_ticks=2,
        ticks_to_stockout=10.0,
        tick_consumption=100.0,
        needed_liters=4000.0,
    )
    assert binding == "STATION_ULLAGE_HEADROOM"


def test_find_service_level_thresholds():
    data = [
        {"multiplier": 1.0, "service_level": 1.0},
        {"multiplier": 1.4, "service_level": 0.995},
        {"multiplier": 1.8, "service_level": 0.96},
        {"multiplier": 2.2, "service_level": 0.92},
        {"multiplier": 2.6, "service_level": 0.88},
    ]
    thresholds = find_service_level_thresholds(data, x_key="multiplier")
    # 99% crosses between 1.4 (0.995) and 1.8 (0.96)
    # 95% crosses between 1.8 (0.96) and 2.2 (0.92)
    # 90% crosses between 2.2 (0.92) and 2.6 (0.88)
    assert thresholds["p99"] is not None
    assert 1.4 <= thresholds["p99"] <= 1.8
    assert thresholds["p95"] is not None
    assert 1.8 <= thresholds["p95"] <= 2.2
    assert thresholds["p90"] is not None
    assert 2.2 <= thresholds["p90"] <= 2.6


def test_identify_binding_constraint_unconstrained():
    binding = identify_binding_constraint(
        depot_stock=50000.0,
        route_max_shipment=6000.0,
        station_ullage=20000.0,
        transit_ticks=2,
        ticks_to_stockout=10.0,
        tick_consumption=200.0,
        needed_liters=2000.0,
    )
    assert binding == "UNCONSTRAINED"


def test_threshold_calculation_deterministic():
    # Verify exact determinism across multiple invocations
    data = [
        {"multiplier": 1.0, "service_level": 1.0},
        {"multiplier": 1.5, "service_level": 0.98},
        {"multiplier": 2.0, "service_level": 0.94},
        {"multiplier": 2.5, "service_level": 0.89},
    ]
    t1 = find_service_level_thresholds(data, x_key="multiplier")
    t2 = find_service_level_thresholds(data, x_key="multiplier")
    assert t1 == t2
    assert t1["p99"] == 1.25
    assert t1["p95"] == 1.875
    assert t1["p90"] == 2.4
