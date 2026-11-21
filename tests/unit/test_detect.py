"""Unit tests for pure detection algorithms."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.detect import (
    detect_abnormal_inventory_changes,
    detect_bottlenecks,
    detect_demand_anomalies,
    detect_emerging_regional_disruptions,
    detect_regional_surges,
    run_all_detectors,
)
from core.forecast import expected_demand
from core.models import (
    Allocation,
    AllocationStatus,
    DemandObs,
    FuelType,
    RouteStatus,
    Snapshot,
    StationStatus,
)

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


def base_snapshot() -> Snapshot:
    raw = {
        name: json.loads((SAMPLES / f"{name}.json").read_text())
        for name in (
            "instance",
            "regions",
            "depots",
            "stations",
            "routes",
            "supply-arrivals",
            "events",
            "metrics",
        )
    }
    raw["supply_arrivals"] = raw.pop("supply-arrivals")
    raw.update(
        allocations=[],
        demand_history=[],
        fetched_at="2026-01-01T00:00:00Z",
        stale=False,
        data_status="HEALTHY",
    )
    return Snapshot.model_validate(raw)


def test_no_false_positives_on_normal_diurnal_swings():
    """Prove 0 demand anomalies and regional surges on normal baseline demand across 96 ticks."""
    snapshot = base_snapshot()
    history: list[DemandObs] = []
    tick_minutes = snapshot.instance.tick_minutes
    obs_id = 1

    for tick in range(1, 97):
        sim_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        for station in snapshot.stations:
            for fuel in (FuelType.DIESEL, FuelType.PETROL, FuelType.OCTANE):
                base = expected_demand(
                    station.demand_profile,
                    fuel.value,
                    sim_time,
                    multiplier=1.0,
                    tick_minutes=tick_minutes,
                )
                history.append(
                    DemandObs(
                        id=obs_id,
                        tick=tick,
                        sim_time=sim_time,
                        station_id=station.id,
                        fuel_type=fuel,
                        demand_liters=base,
                        served_liters=base,
                        unmet_liters=0.0,
                    )
                )
                obs_id += 1

    normal_snapshot = snapshot.model_copy(update={"demand_history": history})
    anomalies = detect_demand_anomalies(normal_snapshot)
    surges = detect_regional_surges(normal_snapshot, anomalies)

    assert len(anomalies) == 0
    assert len(surges) == 0


def test_demand_anomaly_detected_on_spike():
    """Anomalous demand exceeding 1.3x baseline for 3 ticks triggers incident."""
    snapshot = base_snapshot()
    station = snapshot.stations[0]
    fuel = FuelType.DIESEL
    history: list[DemandObs] = []
    tick_minutes = snapshot.instance.tick_minutes
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    obs_id = 1

    # 4 ticks of 2.0x baseline demand
    for tick in range(10, 14):
        base = expected_demand(
            station.demand_profile,
            fuel.value,
            sim_time,
            multiplier=1.0,
            tick_minutes=tick_minutes,
        )
        history.append(
            DemandObs(
                id=obs_id,
                tick=tick,
                sim_time=sim_time,
                station_id=station.id,
                fuel_type=fuel,
                demand_liters=base * 2.0,
                served_liters=base * 2.0,
                unmet_liters=0.0,
            )
        )
        obs_id += 1

    spike_snapshot = snapshot.model_copy(update={"demand_history": history})
    anomalies = detect_demand_anomalies(spike_snapshot)

    assert len(anomalies) == 1
    inc = anomalies[0]
    assert inc.type == "demand_anomaly"
    assert inc.severity == "WARNING"
    assert inc.entity_id == f"{station.id}:{fuel.value}"
    assert inc.dedup_key == f"demand_anomaly:{station.id}:{fuel.value}"
    assert "Anomalous demand surge" in inc.explanation
    assert inc.evidence["consecutive_ticks"] == 3


def test_regional_surge_detected_when_two_stations_surge():
    """Coordinated surge flagged when 2+ stations in the same region surge."""
    snapshot = base_snapshot()
    region_id = snapshot.regions[0].id
    reg_stations = [s for s in snapshot.stations if s.region_id == region_id]
    assert len(reg_stations) >= 2

    history: list[DemandObs] = []
    tick_minutes = snapshot.instance.tick_minutes
    sim_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    obs_id = 100

    for st in reg_stations[:2]:
        for tick in range(10, 14):
            base = expected_demand(
                st.demand_profile,
                FuelType.DIESEL.value,
                sim_time,
                multiplier=1.0,
                tick_minutes=tick_minutes,
            )
            history.append(
                DemandObs(
                    id=obs_id,
                    tick=tick,
                    sim_time=sim_time,
                    station_id=st.id,
                    fuel_type=FuelType.DIESEL,
                    demand_liters=base * 2.0,
                    served_liters=base * 2.0,
                    unmet_liters=0.0,
                )
            )
            obs_id += 1

    surge_snapshot = snapshot.model_copy(update={"demand_history": history})
    anomalies = detect_demand_anomalies(surge_snapshot)
    surges = detect_regional_surges(surge_snapshot, anomalies)

    assert len(anomalies) >= 2
    assert len(surges) == 1
    assert surges[0].type == "regional_surge"
    assert surges[0].severity == "CRITICAL"
    assert surges[0].entity_id == region_id


def test_station_outage_does_not_trigger_abnormal_inventory_false_positive():
    """Stations in OUTAGE status must not produce abnormal inventory false positives."""
    snapshot = base_snapshot()
    stations = [s.model_copy() for s in snapshot.stations]
    stations[0].status = StationStatus.OUTAGE
    outage_snapshot = snapshot.model_copy(update={"stations": stations})

    incidents = detect_abnormal_inventory_changes(outage_snapshot)
    outage_station_id = stations[0].id
    flagged = [i for i in incidents if i.evidence.get("station_id") == outage_station_id]
    assert len(flagged) == 0


def test_bottleneck_detection_dispatch_and_supply():
    """Depot dispatch >= 80% or projected 24h deficit triggers bottleneck."""
    snapshot = base_snapshot()
    depot = snapshot.depots[0]

    # Create allocation utilizing 90% of depot dispatch capacity
    alloc = Allocation(
        id=999,
        idempotency_key="alloc-test-999",
        source_depot_id=depot.id,
        destination_station_id=snapshot.stations[0].id,
        route_id=snapshot.routes[0].id,
        fuel_type=FuelType.DIESEL,
        quantity=depot.dispatch_capacity_per_tick * 0.90,
        status=AllocationStatus.PENDING,
        created_tick=snapshot.instance.tick,
        departure_tick=None,
        expected_arrival_tick=snapshot.instance.tick + 2,
        actual_arrival_tick=None,
        failure_reason=None,
    )
    dispatch_snapshot = snapshot.model_copy(update={"allocations": [alloc]})
    bottlenecks = detect_bottlenecks(dispatch_snapshot)

    dispatch_bottlenecks = [
        b for b in bottlenecks if b.dedup_key == f"bottleneck:dispatch:{depot.id}"
    ]
    assert len(dispatch_bottlenecks) == 1
    assert dispatch_bottlenecks[0].severity == "WARNING"


def test_emerging_regional_disruption():
    """Station outages or 2+ disrupted routes into region trigger disruption incidents."""
    snapshot = base_snapshot()
    region_id = snapshot.regions[0].id
    reg_stations = [s for s in snapshot.stations if s.region_id == region_id]
    routes = [r.model_copy() for r in snapshot.routes]

    # Find routes heading to this region's stations
    reg_station_ids = {s.id for s in reg_stations}
    corridor_routes = [r for r in routes if r.destination_station_id in reg_station_ids]
    assert len(corridor_routes) >= 2
    corridor_routes[0].status = RouteStatus.DISRUPTED
    corridor_routes[1].status = RouteStatus.DISRUPTED

    disruption_snapshot = snapshot.model_copy(update={"routes": routes})
    disruptions = detect_emerging_regional_disruptions(disruption_snapshot)

    corridor_disruptions = [
        d for d in disruptions if d.dedup_key == f"disruption:routes:{region_id}"
    ]
    assert len(corridor_disruptions) == 1
    assert corridor_disruptions[0].severity == "CRITICAL"


def test_run_all_detectors_deduplication():
    """run_all_detectors deduplicates items by dedup_key."""
    snapshot = base_snapshot()
    results = run_all_detectors(snapshot)
    keys = [r.dedup_key for r in results]
    assert len(keys) == len(set(keys))
