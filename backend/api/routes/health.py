"""Operator-facing component health aggregation from persisted state and bounded probes."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Request

from api.database import ReadRepository
from core.metrics import api_http_request_duration, api_http_requests

router = APIRouter(prefix="/api")


def _age_seconds(value: datetime | str | None) -> float | None:
    if value is None:
        return None
    parsed = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds())


def _status(age: float | None, data_status: str | None = None) -> str:
    if age is None or age > 120:
        return "OFFLINE"
    if age >= 15 or data_status not in (None, "HEALTHY"):
        return "DEGRADED"
    return "HEALTHY"


def _latency_summary() -> dict[str, float]:
    samples = [
        sample for family in api_http_request_duration.collect() for sample in family.samples
    ]
    count = sum(sample.value for sample in samples if sample.name.endswith("_count"))
    target = count * 0.95
    buckets: dict[float, float] = {}
    for sample in samples:
        if sample.name.endswith("_bucket"):
            le = sample.labels.get("le")
            if le is not None and le != "+Inf":
                buckets[float(le)] = buckets.get(float(le), 0.0) + sample.value
    p95 = next(
        (bound for bound, observed in sorted(buckets.items()) if observed >= target),
        max(buckets, default=0.0),
    )

    counters = [sample for family in api_http_requests.collect() for sample in family.samples]
    total = sum(sample.value for sample in counters if sample.name.endswith("_total"))
    errors = sum(
        sample.value
        for sample in counters
        if sample.name.endswith("_total") and sample.labels.get("status_class") == "5xx"
    )
    return {"p95_seconds": p95, "error_rate": (errors / total if total else 0.0)}


async def _predictor_status() -> str:
    base_url = os.getenv("PREDICTOR_URL", "http://predictor:8103").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            response = await client.get(f"{base_url}/health")
        if response.status_code != 200:
            return "DEGRADED"
        payload = response.json()
        if isinstance(payload, dict) and payload.get("status") == "ok":
            return "HEALTHY"
        return "DEGRADED"
    except httpx.HTTPError:
        return "OFFLINE"
    except ValueError:
        return "DEGRADED"


async def _component_from_heartbeat(
    repository: ReadRepository, component: str
) -> tuple[str, float | None, dict[str, Any]]:
    try:
        record = await repository.get_heartbeat(component)
    except Exception:
        return "OFFLINE", None, {}
    if record is None:
        return "OFFLINE", None, {}
    detail = record.get("detail") or {}
    age = _age_seconds(record.get("last_seen"))
    return _status(age, detail.get("data_status")), age, detail


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    repository: ReadRepository | None = getattr(request.app.state, "repository", None)
    checked_at = datetime.now(timezone.utc).isoformat()
    components: dict[str, dict[str, Any]] = {
        "backend": {"status": "HEALTHY", "age_seconds": 0.0},
        "predictor": {"status": await _predictor_status(), "age_seconds": None},
    }
    if repository is None:
        components.update(
            {
                "database": {"status": "OFFLINE", "age_seconds": None},
                "worker": {"status": "OFFLINE", "age_seconds": None},
                "simulator": {"status": "OFFLINE", "age_seconds": None},
                "decision_engine": {"status": "OFFLINE", "age_seconds": None},
            }
        )
    else:
        try:
            db_ok = await repository.check_database()
        except Exception:
            db_ok = False
        components["database"] = {
            "status": "HEALTHY" if db_ok else "OFFLINE",
            "age_seconds": None,
        }
        worker_status, worker_age, detail = await _component_from_heartbeat(repository, "worker")
        components["worker"] = {"status": worker_status, "age_seconds": worker_age}
        breaker = detail.get("breaker_state")
        if worker_status == "HEALTHY" and breaker in ("OPEN", "HALF_OPEN"):
            worker_status = "DEGRADED"
        if detail.get("last_ingest_ok") is False and worker_status == "HEALTHY":
            worker_status = "DEGRADED"
        try:
            latest = await repository.get_latest_snapshot()
            snapshot_age = _age_seconds(latest.get("fetched_at")) if latest else None
            snapshot_status = str(latest.get("data_status", "OFFLINE")) if latest else "OFFLINE"
            if latest and latest.get("stale"):
                snapshot_status = "DEGRADED"
            simulator_status = _status(snapshot_age, snapshot_status)
            if worker_status == "OFFLINE":
                simulator_status = "OFFLINE"
            elif worker_status == "DEGRADED" and simulator_status == "HEALTHY":
                simulator_status = "DEGRADED"
        except Exception:
            snapshot_age = None
            simulator_status = "OFFLINE"
        components["simulator"] = {"status": simulator_status, "age_seconds": snapshot_age}
        engine_status, engine_age, _ = await _component_from_heartbeat(
            repository, "decision_engine"
        )
        # The decision pipeline shares the worker process. A stale pipeline
        # heartbeat means processing is degraded; the worker heartbeat is the
        # signal for process availability.
        if worker_status != "OFFLINE" and engine_status == "OFFLINE":
            engine_status = "DEGRADED"
        components["decision_engine"] = {"status": engine_status, "age_seconds": engine_age}

    statuses = [item["status"] for item in components.values()]
    if "OFFLINE" in statuses:
        overall = "OFFLINE"
    elif "DEGRADED" in statuses:
        overall = "DEGRADED"
    else:
        overall = "HEALTHY"
    return {
        "status": overall,
        "components": components,
        "last_check_at": checked_at,
        "latency": _latency_summary(),
        "simulated": True,
    }
