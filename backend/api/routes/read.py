"""Operator read endpoints. These routes only query the local database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from api.database import ReadRepository
from core.models import FuelType

router = APIRouter(prefix="/api")


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
