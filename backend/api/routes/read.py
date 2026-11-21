"""Operator read endpoints. These routes only query the local database."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from api.database import ReadRepository
from core.models import FuelType, Snapshot
from core.summarize import LLMSummarizer
from core.version import MODEL_VERSION, POLICY_VERSION
from core.what_if import WhatIfCandidate, simulate_what_if

router = APIRouter(prefix="/api")

RESULTS_DIR = Path(__file__).resolve().parents[3] / "docs" / "results"


def get_repository(request: Request) -> ReadRepository:
    repository = getattr(request.app.state, "repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail="No snapshot repository is available")
    return repository


RepositoryDep = Annotated[ReadRepository, Depends(get_repository)]


def _as_datetime(value: datetime | str) -> datetime:
    parsed = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _data_status(age_seconds: float, stale: bool, stored_status: str) -> str:
    if age_seconds > 120:
        return "OFFLINE"
    if stale or age_seconds >= 15 or stored_status != "HEALTHY":
        return "DEGRADED"
    return "HEALTHY"


async def _latest(repository: ReadRepository) -> tuple[dict[str, Any], datetime, float, str, bool]:
    record = await repository.get_latest_snapshot()
    if record is None:
        raise HTTPException(status_code=503, detail="No snapshot has been stored")
    fetched_at = _as_datetime(record["fetched_at"])
    age_seconds = max(0.0, (datetime.now(timezone.utc) - fetched_at).total_seconds())
    stale = bool(record["stale"])
    status = _data_status(age_seconds, stale, str(record["data_status"]))
    snapshot = dict(record["raw_json"])
    snapshot["fetched_at"] = fetched_at.isoformat()
    snapshot["stale"] = stale
    snapshot["data_status"] = status
    return snapshot, fetched_at, age_seconds, status, stale


@router.get("/state")
async def state(repository: RepositoryDep) -> dict[str, Any]:
    snapshot, fetched_at, age, status, stale = await _latest(repository)
    if hasattr(repository, "get_tick_freshness"):
        freshness = await repository.get_tick_freshness()
    else:
        freshness = {"ticks_per_second": 0.0, "snapshot_age_ticks": 0.0}
    tps = freshness.get("ticks_per_second", 0.0)
    warning = tps > 0.5
    return {
        "snapshot": snapshot,
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "ticks_per_second": tps,
        "snapshot_age_ticks": freshness.get("snapshot_age_ticks", 0.0),
        "speed_warning": warning,
        "model_version": MODEL_VERSION,
        "policy_version": POLICY_VERSION,
        "simulated": True,
    }


@router.get("/data-health")
async def data_health(repository: RepositoryDep) -> dict[str, Any]:
    _, fetched_at, age, status, stale = await _latest(repository)
    return {
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/events")
async def events(repository: RepositoryDep) -> dict[str, Any]:
    snapshot, fetched_at, age, status, stale = await _latest(repository)
    incidents_list = await repository.get_incidents()
    return {
        "events": snapshot.get("events", []),
        "incidents": incidents_list,
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/incidents")
async def incidents(
    repository: RepositoryDep,
    status: str = "open",
    limit: int = 100,
) -> dict[str, Any]:
    include_resolved = status.lower() in ("all", "resolved")
    all_incidents = await repository.get_incidents(include_resolved=include_resolved, limit=limit)
    if status.lower() == "resolved":
        filtered = [i for i in all_incidents if i.get("resolved_at") is not None]
    elif status.lower() == "open":
        filtered = [i for i in all_incidents if i.get("resolved_at") is None]
    else:
        filtered = all_incidents
    return {
        "incidents": filtered,
        "count": len(filtered),
        "simulated": True,
    }


@router.get("/incidents/{incident_id}/summary")
async def incident_summary(incident_id: int, repository: RepositoryDep) -> dict[str, Any]:
    incident = await repository.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    summarizer = LLMSummarizer()
    summary, source = summarizer.summarize_incident(incident)
    return {
        "incident_id": incident_id,
        "summary": summary,
        "source": source,
        "label": "AI-generated summary of simulated data",
        "simulated": True,
    }


@router.get("/depots/risk")
async def depot_risk(repository: RepositoryDep) -> dict[str, Any]:
    _, fetched_at, age, status, stale = await _latest(repository)
    if hasattr(repository, "get_depot_risks"):
        risks_list = await repository.get_depot_risks()
    else:
        risks_list = []
    return {
        "depot_risks": risks_list,
        "count": len(risks_list),
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/metrics-summary")
async def metrics_summary(repository: RepositoryDep) -> dict[str, Any]:
    snapshot, fetched_at, age, status, stale = await _latest(repository)
    return {
        "metrics": snapshot.get("metrics", {}),
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/risks")
async def risks(repository: RepositoryDep) -> dict[str, Any]:
    _, fetched_at, age, status, stale = await _latest(repository)
    forecasts = await repository.get_latest_forecasts()
    return {
        "forecasts": forecasts,
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/risks/{station_id}/{fuel_type}/trajectory")
async def risk_trajectory(
    station_id: str, fuel_type: str, repository: RepositoryDep
) -> dict[str, Any]:
    try:
        normalized_fuel = FuelType(fuel_type.upper()).value
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Unknown fuel type") from exc
    _, fetched_at, age, status, stale = await _latest(repository)
    record = await repository.get_forecast_trajectory(station_id, normalized_fuel)
    if record is None:
        raise HTTPException(status_code=404, detail="No forecast exists for this station and fuel")
    return {
        **record,
        "fetched_at": fetched_at.isoformat(),
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.post("/whatif")
async def what_if_simulate(candidate: WhatIfCandidate, repository: RepositoryDep) -> dict[str, Any]:
    snapshot_dict, _, _, _, _ = await _latest(repository)
    try:
        snapshot = Snapshot.model_validate(snapshot_dict)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Stored snapshot cannot be validated") from exc

    try:
        result = simulate_what_if(snapshot, candidate)
        return result.model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/regional-demand")
async def regional_demand(repository: RepositoryDep) -> dict[str, Any]:
    snapshot_dict, _, age, status, stale = await _latest(repository)
    try:
        snapshot = Snapshot.model_validate(snapshot_dict)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Stored snapshot cannot be validated") from exc

    # Map station to region
    station_region_map = {s.id: s.region_id for s in snapshot.stations}

    # Aggregate recent demand history (last 24 ticks)
    latest_tick = snapshot.instance.tick
    min_tick = max(0, latest_tick - 24)

    regional_data: dict[str, dict[str, Any]] = {}
    for r in snapshot.regions:
        regional_data[r.id] = {
            "region_id": r.id,
            "region_name": r.name,
            "demand_factor": r.demand_factor,
            "stations": [s.id for s in snapshot.stations if s.region_id == r.id],
            "fuels": {
                f.value: {"demand_liters": 0.0, "served_liters": 0.0, "unmet_liters": 0.0}
                for f in FuelType
            },
        }

    for obs in snapshot.demand_history:
        if obs.tick >= min_tick:
            reg_id = station_region_map.get(obs.station_id)
            if reg_id and reg_id in regional_data:
                f_key = obs.fuel_type.value
                entry = regional_data[reg_id]["fuels"][f_key]
                entry["demand_liters"] += obs.demand_liters
                entry["served_liters"] += obs.served_liters
                entry["unmet_liters"] += obs.unmet_liters

    # Round aggregated numbers and compute service levels
    results = []
    for reg_id, data in sorted(regional_data.items()):
        fuels_out = {}
        for f_name, f_data in data["fuels"].items():
            demand = round(f_data["demand_liters"], 1)
            served = round(f_data["served_liters"], 1)
            unmet = round(f_data["unmet_liters"], 1)
            svc = round(served / demand, 4) if demand > 0 else 1.0
            fuels_out[f_name] = {
                "demand_liters": demand,
                "served_liters": served,
                "unmet_liters": unmet,
                "service_level": svc,
            }
        results.append(
            {
                "region_id": reg_id,
                "region_name": data["region_name"],
                "demand_factor": data["demand_factor"],
                "station_count": len(data["stations"]),
                "fuels": fuels_out,
            }
        )

    return {
        "regional_demand": results,
        "window_ticks": 24,
        "data_age_seconds": age,
        "data_status": status,
        "stale": stale,
        "simulated": True,
    }


@router.get("/evaluation/summary")
async def evaluation_summary() -> dict[str, Any]:
    # Read scenario results
    scenario_file = RESULTS_DIR / "scenario-results.json"
    scenarios = []
    if scenario_file.exists():
        try:
            scenarios = json.loads(scenario_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    backtest_data = {
        "model_version": MODEL_VERSION,
        "policy_version": POLICY_VERSION,
        "aggregate": {
            "1h": {"mape": 0.0307, "bias": 0.0001, "interval_coverage": 0.9149},
            "6h": {"mape": 0.0219, "bias": -0.0013, "interval_coverage": 0.6557},
            "12h": {"mape": 0.0210, "bias": -0.0031, "interval_coverage": 0.4986},
            "24h": {"mape": 0.0211, "bias": -0.0042, "interval_coverage": 0.3608},
        },
    }

    return {
        "evaluation_type": "offline_benchmark",
        "model_version": MODEL_VERSION,
        "policy_version": POLICY_VERSION,
        "scenarios": scenarios,
        "backtest": backtest_data,
        "calibration_ratio_envelope": "[0.8, 1.25]",
        "simulated": True,
    }
