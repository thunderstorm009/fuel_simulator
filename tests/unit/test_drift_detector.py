"""Unit tests for pure calibration drift detection."""

from __future__ import annotations

from datetime import datetime, timezone

from core.detect import detect_calibration_drift
from core.forecast import expected_demand
from core.models import (
    DataStatus,
    DemandObs,
    FuelType,
    Instance,
    InstanceStatus,
    Metrics,
    Snapshot,
    Station,
    StationStatus,
)


def _make_snapshot(
    demand_records: list[DemandObs],
    station_status: StationStatus = StationStatus.OPEN,
) -> Snapshot:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    station = Station(
        id="station-mirpur",
        name="Mirpur Fuel Station",
        region_id="region-dhaka",
        status=station_status,
        demand_profile="urban_high",
        demand_multiplier=1.0,
        capacity={FuelType.DIESEL: 50000.0, FuelType.PETROL: 40000.0, FuelType.OCTANE: 30000.0},
        inventory={FuelType.DIESEL: 20000.0, FuelType.PETROL: 15000.0, FuelType.OCTANE: 10000.0},
    )
    inst = Instance(
        id=1,
        scenario_id="baseline",
        scenario_version="1.0",
        tick=len(demand_records),
        sim_time=sim_time,
        status=InstanceStatus.RUNNING,
        tick_minutes=15,
        speed=1.0,
        seed=42,
    )
    return Snapshot(
        instance=inst,
        regions=[],
        depots=[],
        stations=[station],
        routes=[],
        supply_arrivals=[],
        events=[],
        allocations=[],
        demand_history=demand_records,
        metrics=Metrics(
            served_demand_liters=1000.0,
            unmet_demand_liters=0.0,
            service_level=1.0,
            allocation_liters=0.0,
            allocation_failures=0,
        ),
        fetched_at=sim_time,
        stale=False,
        data_status=DataStatus.HEALTHY,
    )


def test_drift_detector_normal_no_incident() -> None:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    base = expected_demand("urban_high", "DIESEL", sim_time, 1.0, 15)
    records = [
        DemandObs(
            id=i,
            station_id="station-mirpur",
            fuel_type=FuelType.DIESEL,
            tick=i,
            sim_time=sim_time,
            demand_liters=base * 1.02,
            served_liters=base * 1.02,
            unmet_liters=0.0,
        )
        for i in range(1, 10)
    ]
    snapshot = _make_snapshot(records)
    incidents = detect_calibration_drift(snapshot, threshold_ticks=4)
    assert len(incidents) == 0


def test_drift_detector_sustained_surge_triggers_incident() -> None:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    base = expected_demand("urban_high", "DIESEL", sim_time, 1.0, 15)
    # Demand is 1.6x baseline for 5 ticks (> 1.25 upper threshold)
    records = [
        DemandObs(
            id=i,
            station_id="station-mirpur",
            fuel_type=FuelType.DIESEL,
            tick=i,
            sim_time=sim_time,
            demand_liters=base * 1.6,
            served_liters=base * 1.6,
            unmet_liters=0.0,
        )
        for i in range(1, 6)
    ]
    snapshot = _make_snapshot(records)
    incidents = detect_calibration_drift(snapshot, threshold_ticks=4)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.type == "calibration_drift"
    assert inc.severity == "WARNING"
    assert inc.evidence["direction"] == "SURGE"
    assert inc.evidence["station_id"] == "station-mirpur"


def test_drift_detector_sustained_drop_triggers_incident() -> None:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    base = expected_demand("urban_high", "DIESEL", sim_time, 1.0, 15)
    # Demand is 0.5x baseline for 5 ticks (< 0.8 lower threshold)
    records = [
        DemandObs(
            id=i,
            station_id="station-mirpur",
            fuel_type=FuelType.DIESEL,
            tick=i,
            sim_time=sim_time,
            demand_liters=base * 0.5,
            served_liters=base * 0.5,
            unmet_liters=0.0,
        )
        for i in range(1, 6)
    ]
    snapshot = _make_snapshot(records)
    incidents = detect_calibration_drift(snapshot, threshold_ticks=4)
    assert len(incidents) == 1
    assert incidents[0].evidence["direction"] == "COLLAPSE"


def test_drift_detector_outage_ignored() -> None:
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    base = expected_demand("urban_high", "DIESEL", sim_time, 1.0, 15)
    records = [
        DemandObs(
            id=i,
            station_id="station-mirpur",
            fuel_type=FuelType.DIESEL,
            tick=i,
            sim_time=sim_time,
            demand_liters=base * 0.2,
            served_liters=0.0,
            unmet_liters=base * 0.2,
        )
        for i in range(1, 6)
    ]
    snapshot = _make_snapshot(records, station_status=StationStatus.OUTAGE)
    incidents = detect_calibration_drift(snapshot, threshold_ticks=4)
    assert len(incidents) == 0
