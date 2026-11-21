"""Pure detection algorithms for anomalies, bottlenecks, and emerging disruptions.

Pure functions only: zero I/O, no network or database calls, deterministic and testable.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from core.depot_risk import DepotRiskProjection, calculate_depot_risks
from core.forecast import expected_demand
from core.models import (
    DemandObs,
    FuelType,
    Snapshot,
    StationStatus,
)
from core.world import PROFILE_NOISE


@dataclass(frozen=True)
class IncidentDetection:
    type: str  # 'demand_anomaly', 'regional_surge', 'bottleneck', etc.
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'
    entity_id: str
    dedup_key: str
    explanation: str
    recovery_condition: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_demand_anomalies(snapshot: Snapshot) -> list[IncidentDetection]:
    """Flag demand anomaly when observed demand exceeds expected baseline (>1.3x) for 3 ticks.

    The expected baseline uses station profile and diurnal factor WITHOUT station multiplier.
    Noise floor from profile is enforced to prevent false positives.
    """
    incidents: list[IncidentDetection] = []
    tick_minutes = max(1, snapshot.instance.tick_minutes)

    for station in snapshot.stations:
        noise = PROFILE_NOISE.get(station.demand_profile, 0.10)
        noise_floor = 1.0 + noise

        for fuel in (FuelType.DIESEL, FuelType.PETROL, FuelType.OCTANE):
            obs = [
                d
                for d in snapshot.demand_history
                if d.station_id == station.id and d.fuel_type is fuel
            ]
            obs.sort(key=lambda d: d.tick)

            if len(obs) < 3:
                continue

            recent_obs = obs[-4:]
            ratios: list[float] = []
            for d in recent_obs:
                base = expected_demand(
                    station.demand_profile,
                    fuel.value,
                    d.sim_time,
                    multiplier=1.0,
                    tick_minutes=tick_minutes,
                )
                ratio = d.demand_liters / max(1.0, base)
                ratios.append(ratio)

            if len(ratios) >= 3 and all(r > 1.3 and r > noise_floor for r in ratios[-3:]):
                avg_ratio = sum(ratios[-3:]) / 3.0
                incidents.append(
                    IncidentDetection(
                        type="demand_anomaly",
                        severity="WARNING",
                        entity_id=f"{station.id}:{fuel.value}",
                        dedup_key=f"demand_anomaly:{station.id}:{fuel.value}",
                        explanation=(
                            f"Anomalous demand surge detected at {station.name} for {fuel.value}. "
                            f"Observed demand averaged {avg_ratio:.2f}x baseline for 3 ticks."
                        ),
                        recovery_condition="Demand returns below 1.3x baseline for 2 ticks.",
                        evidence={
                            "station_id": station.id,
                            "fuel_type": fuel.value,
                            "profile": station.demand_profile,
                            "consecutive_ticks": 3,
                            "recent_ratios": [round(r, 3) for r in ratios[-3:]],
                            "noise_floor": round(noise_floor, 3),
                        },
                    )
                )

    return incidents


def detect_regional_surges(
    snapshot: Snapshot,
    demand_anomalies: Sequence[IncidentDetection] | None = None,
) -> list[IncidentDetection]:
    """Flag regional surge when 2+ stations in one region show demand anomalies within 8 ticks."""
    if demand_anomalies is None:
        demand_anomalies = detect_demand_anomalies(snapshot)

    incidents: list[IncidentDetection] = []
    flagged_station_ids = {a.entity_id.split(":")[0] for a in demand_anomalies}

    for region in snapshot.regions:
        stations_in_region = [s for s in snapshot.stations if s.region_id == region.id]
        flagged_in_region = [s for s in stations_in_region if s.id in flagged_station_ids]

        if len(flagged_in_region) >= 2:
            station_names = ", ".join(s.name for s in flagged_in_region)
            incidents.append(
                IncidentDetection(
                    type="regional_surge",
                    severity="CRITICAL",
                    entity_id=region.id,
                    dedup_key=f"regional_surge:{region.id}",
                    explanation=(
                        f"Coordinated regional demand surge in {region.name}. "
                        f"Multiple filling stations ({station_names}) surging simultaneously."
                    ),
                    recovery_condition="Fewer than 2 regional stations remain flagged.",
                    evidence={
                        "region_id": region.id,
                        "flagged_stations": [s.id for s in flagged_in_region],
                        "total_stations_in_region": len(stations_in_region),
                    },
                )
            )

    return incidents


def detect_abnormal_inventory_changes(snapshot: Snapshot) -> list[IncidentDetection]:
    """Flag unexpected inventory drop or gain that consumption/arrivals do not explain.

    Station outage must NOT trigger this detector (zero demand and freeze is normal).
    """
    incidents: list[IncidentDetection] = []
    tick_minutes = max(1, snapshot.instance.tick_minutes)

    for station in snapshot.stations:
        if getattr(station.status, "value", station.status) in {"OUTAGE", "CLOSED"}:
            continue

        for fuel in (FuelType.DIESEL, FuelType.PETROL, FuelType.OCTANE):
            obs = [
                d
                for d in snapshot.demand_history
                if d.station_id == station.id and d.fuel_type is fuel
            ]
            obs.sort(key=lambda d: d.tick)

            if len(obs) < 2:
                continue

            last_obs = obs[-1]
            prev_obs = obs[-2]
            if last_obs.tick - prev_obs.tick != 1:
                continue

            base_expected = expected_demand(
                station.demand_profile,
                fuel.value,
                last_obs.sim_time,
                station.demand_multiplier,
                tick_minutes,
            )

            arrivals_volume = sum(
                a.quantity
                for a in snapshot.allocations
                if a.destination_station_id == station.id
                and a.fuel_type is fuel
                and a.actual_arrival_tick == last_obs.tick
            )

            noise = PROFILE_NOISE.get(station.demand_profile, 0.10)
            tolerance = max(300.0, base_expected * (1.0 + 3.0 * noise))
            unexplained_loss = (last_obs.demand_liters - last_obs.served_liters) - tolerance
            if unexplained_loss > 1000.0 and arrivals_volume == 0:
                incidents.append(
                    IncidentDetection(
                        type="abnormal_inventory",
                        severity="WARNING",
                        entity_id=f"{station.id}:{fuel.value}",
                        dedup_key=f"abnormal_inventory:{station.id}:{fuel.value}",
                        explanation=(
                            f"Abnormal inventory drop at {station.name} for {fuel.value}. "
                            f"Unexplained volume variance of {unexplained_loss:.0f}L detected."
                        ),
                        recovery_condition="Station inventory balance reconciles within tolerance.",
                        evidence={
                            "station_id": station.id,
                            "fuel_type": fuel.value,
                            "unexplained_liters": round(unexplained_loss, 1),
                            "tolerance": round(tolerance, 1),
                        },
                    )
                )

    return incidents


def detect_bottlenecks(
    snapshot: Snapshot,
    depot_risks: Sequence[DepotRiskProjection] | None = None,
) -> list[IncidentDetection]:
    """Flag depot dispatch capacity >= 80% or depot 24h projected station deficit."""
    incidents: list[IncidentDetection] = []
    if depot_risks is None:
        depot_risks = calculate_depot_risks(snapshot)

    # Check dispatch bottleneck per depot
    depot_dispatch_checked: set[str] = set()
    for risk in depot_risks:
        if risk.depot_id not in depot_dispatch_checked:
            depot_dispatch_checked.add(risk.depot_id)
            if risk.dispatch_utilization >= 0.80:
                incidents.append(
                    IncidentDetection(
                        type="bottleneck",
                        severity="WARNING",
                        entity_id=risk.depot_id,
                        dedup_key=f"bottleneck:dispatch:{risk.depot_id}",
                        explanation=(
                            f"High dispatch utilization at {risk.depot_name} "
                            f"({risk.dispatch_utilization * 100:.1f}%)."
                        ),
                        recovery_condition="Depot dispatch utilization drops below 70%.",
                        evidence={
                            "depot_id": risk.depot_id,
                            "utilization": risk.dispatch_utilization,
                            "dispatch_capacity": risk.evidence.get("dispatch_capacity"),
                        },
                    )
                )

        # Supply deficit bottleneck per fuel
        if risk.net_cover_liters < 0:
            deficit = abs(risk.net_cover_liters)
            avail = risk.current_inventory + risk.scheduled_arrivals
            incidents.append(
                IncidentDetection(
                    type="bottleneck",
                    severity="CRITICAL",
                    entity_id=f"{risk.depot_id}:{risk.fuel_type}",
                    dedup_key=f"bottleneck:supply:{risk.depot_id}:{risk.fuel_type}",
                    explanation=(
                        f"Supply deficit projected at {risk.depot_name} for {risk.fuel_type}. "
                        f"Served 24h demand ({risk.projected_demand:.0f}L) exceeds "
                        f"depot stock + arrivals ({avail:.0f}L)."
                    ),
                    recovery_condition="Depot reserves plus arrivals exceed 24h demand.",
                    evidence={
                        "depot_id": risk.depot_id,
                        "fuel_type": risk.fuel_type,
                        "depot_stock": risk.current_inventory,
                        "scheduled_arrivals": risk.scheduled_arrivals,
                        "projected_need_24h": risk.projected_demand,
                        "deficit_liters": round(deficit, 1),
                        "cover_hours": risk.cover_hours,
                    },
                )
            )

    return incidents


def detect_emerging_regional_disruptions(snapshot: Snapshot) -> list[IncidentDetection]:
    """Flag station outages or 2+ disrupted routes into a region."""
    incidents: list[IncidentDetection] = []

    for region in snapshot.regions:
        stations_in_region = [s for s in snapshot.stations if s.region_id == region.id]
        station_id_map = {s.id: s for s in stations_in_region}

        outages = [
            s
            for s in stations_in_region
            if getattr(s.status, "value", s.status) in {"OUTAGE", "CLOSED"}
        ]
        if outages:
            names = ", ".join(s.name for s in outages)
            incidents.append(
                IncidentDetection(
                    type="emerging_regional_disruption",
                    severity="CRITICAL",
                    entity_id=region.id,
                    dedup_key=f"disruption:outage:{region.id}",
                    explanation=(
                        f"Regional infrastructure disruption in {region.name}: "
                        f"Filling station outage active at {names}."
                    ),
                    recovery_condition="All station outages in region resolve to OPEN.",
                    evidence={
                        "region_id": region.id,
                        "outage_stations": [s.id for s in outages],
                    },
                )
            )

        routes_to_region = [
            r for r in snapshot.routes if r.destination_station_id in station_id_map
        ]
        disrupted_routes = [
            r
            for r in routes_to_region
            if getattr(r.status, "value", r.status) in {"DISRUPTED", "BLOCKED"}
        ]

        if len(disrupted_routes) >= 2:
            r_ids = ", ".join(r.id for r in disrupted_routes)
            incidents.append(
                IncidentDetection(
                    type="emerging_regional_disruption",
                    severity="CRITICAL",
                    entity_id=region.id,
                    dedup_key=f"disruption:routes:{region.id}",
                    explanation=(
                        f"Corridor failure in {region.name}: "
                        f"Multiple transport routes ({r_ids}) currently disrupted."
                    ),
                    recovery_condition="Fewer than 2 transport routes remain disrupted.",
                    evidence={
                        "region_id": region.id,
                        "disrupted_routes": [r.id for r in disrupted_routes],
                    },
                )
            )

    return incidents


def detect_calibration_drift(
    snapshot: Snapshot,
    threshold_ticks: int = 4,
    lower: float = 0.8,
    upper: float = 1.25,
) -> list[IncidentDetection]:
    """Detect sustained forecast calibration ratio drift outside [0.8, 1.25]
    for >= threshold_ticks consecutive ticks.
    """
    incidents: list[IncidentDetection] = []
    obs_by_station_fuel: dict[tuple[str, FuelType], list[DemandObs]] = {}
    for obs in snapshot.demand_history:
        obs_by_station_fuel.setdefault((obs.station_id, obs.fuel_type), []).append(obs)

    stations_by_id = {s.id: s for s in snapshot.stations}

    for (station_id, fuel), history in obs_by_station_fuel.items():
        station = stations_by_id.get(station_id)
        if not station or station.status == StationStatus.OUTAGE:
            continue
        sorted_history = sorted(history, key=lambda o: o.tick)
        if len(sorted_history) < threshold_ticks:
            continue

        recent = sorted_history[-threshold_ticks:]
        ratios: list[float] = []
        for obs in recent:
            base_expected = expected_demand(
                profile=station.demand_profile,
                fuel=fuel.value,
                sim_time=obs.sim_time,
                multiplier=1.0,
                tick_minutes=snapshot.instance.tick_minutes,
            )
            if base_expected > 0:
                ratios.append(obs.demand_liters / base_expected)

        if len(ratios) < threshold_ticks:
            continue

        all_high = all(r > upper for r in ratios)
        all_low = all(r < lower for r in ratios)
        if all_high or all_low:
            direction = "SURGE" if all_high else "COLLAPSE"
            avg_ratio = sum(ratios) / len(ratios)
            incidents.append(
                IncidentDetection(
                    type="calibration_drift",
                    severity="WARNING",
                    entity_id=f"{station_id}:{fuel.value}",
                    dedup_key=f"calibration_drift:{station_id}:{fuel.value}",
                    explanation=(
                        f"Forecast calibration ratio for {station.name} {fuel.value} has drifted "
                        f"({direction}, mean ratio {avg_ratio:.2f}) outside [{lower}, {upper}] for "
                        f"{threshold_ticks} consecutive ticks."
                    ),
                    recovery_condition=(
                        f"Calibration ratio returns to acceptable range [{lower}, {upper}]."
                    ),
                    evidence={
                        "station_id": station_id,
                        "fuel_type": fuel.value,
                        "direction": direction,
                        "mean_ratio": round(avg_ratio, 3),
                        "consecutive_ticks": threshold_ticks,
                        "threshold_lower": lower,
                        "threshold_upper": upper,
                    },
                )
            )
    return incidents


def run_all_detectors(
    snapshot: Snapshot,
    depot_risks: Sequence[DepotRiskProjection] | None = None,
) -> list[IncidentDetection]:
    """Execute all pure detectors and deduplicate by dedup_key."""
    results: list[IncidentDetection] = []
    seen_keys: set[str] = set()

    demand_anomalies = detect_demand_anomalies(snapshot)
    regional_surges = detect_regional_surges(snapshot, demand_anomalies)
    abnormal_inventories = detect_abnormal_inventory_changes(snapshot)
    bottlenecks = detect_bottlenecks(snapshot, depot_risks=depot_risks)
    disruptions = detect_emerging_regional_disruptions(snapshot)
    drifts = detect_calibration_drift(snapshot)

    all_detections = (
        demand_anomalies
        + regional_surges
        + abnormal_inventories
        + bottlenecks
        + disruptions
        + drifts
    )

    for item in all_detections:
        if item.dedup_key not in seen_keys:
            seen_keys.add(item.dedup_key)
            results.append(item)

    return results
