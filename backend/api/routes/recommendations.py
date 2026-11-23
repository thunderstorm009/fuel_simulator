"""Database-backed recommendation reads and human decision writes."""

from __future__ import annotations

import hmac
import json
import os
import time
from collections import defaultdict
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, field_validator

from api.database import ReadRepository
from api.routes.read import RepositoryDep
from core.metrics import recommendations_by_status

router = APIRouter(prefix="/api")

# Sliding-window rate limiter for operator decision actions
_DECISION_CALLS: defaultdict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW_SECONDS: float = 60.0
_RECS_CACHE: tuple[int, bytes] | None = None


def get_rate_limit_max_requests() -> int:
    api_workers = max(1, int(os.getenv("API_WORKERS", "1")))
    configured = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
    return max(10, configured // api_workers)


def check_rate_limit(key: str = "operator") -> None:
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    calls = [t for t in _DECISION_CALLS[key] if t > window_start]
    _DECISION_CALLS[key] = calls
    max_reqs = get_rate_limit_max_requests()
    if len(calls) >= max_reqs:
        detail_msg = (
            f"Too Many Requests: Operator decision rate limit exceeded. Max {max_reqs} per minute."
        )
        raise HTTPException(status_code=429, detail=detail_msg)
    _DECISION_CALLS[key].append(now)


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_must_contain_non_whitespace(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must contain non-whitespace text")
        return normalized


def require_operator_token(
    token: Annotated[str, Header(alias="X-Operator-Token")] = "",
) -> str:
    expected = os.getenv("OPERATOR_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="Operator decisions are not configured")
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid operator token")
    return "operator"


@router.get("/recommendations")
async def recommendations(request: Request, repository: RepositoryDep) -> Response:
    snap_id = 0
    if hasattr(repository, "get_latest_snapshot_meta"):
        meta = await repository.get_latest_snapshot_meta()
        if meta:
            snap_id = int(meta.get("id", 0))
    elif hasattr(repository, "get_latest_snapshot"):
        rec = await repository.get_latest_snapshot()
        if rec:
            snap_id = int(rec.get("id", 0))

    etag = f'W/"snap-{snap_id}"'
    header = request.headers.get("if-none-match", "").strip()
    if snap_id > 0 and header in (etag, f'"snap-{snap_id}"', f"snap-{snap_id}"):
        return Response(status_code=304, headers={"ETag": etag})

    global _RECS_CACHE
    if _RECS_CACHE is not None and _RECS_CACHE[0] == snap_id and snap_id > 0:
        return Response(
            content=_RECS_CACHE[1],
            media_type="application/json",
            headers={"ETag": etag},
        )

    recs = await repository.get_recommendations()
    payload = {"recommendations": jsonable_encoder(recs), "simulated": True}
    raw_bytes = json.dumps(payload).encode("utf-8")
    if snap_id > 0:
        _RECS_CACHE = (snap_id, raw_bytes)
    return Response(content=raw_bytes, media_type="application/json", headers={"ETag": etag})


@router.get("/decisions")
async def decisions(repository: RepositoryDep) -> dict[str, Any]:
    return {"decisions": await repository.get_decisions(), "simulated": True}


async def _decide(
    recommendation_id: UUID,
    action: str,
    reason: str | None,
    actor: str,
    repository: ReadRepository,
) -> dict[str, Any]:
    try:
        result = await repository.decide_recommendation(
            str(recommendation_id), action, reason, actor
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    recommendation = result["recommendation"]
    if result["decision_recorded"]:
        recommendations_by_status.labels(status=recommendation["status"]).inc()
    if recommendation["status"] == "EXPIRED":
        raise HTTPException(status_code=409, detail="Recommendation has expired")
    return {
        "recommendation_id": str(recommendation_id),
        "status": recommendation["status"],
        "already_decided": not result["decision_recorded"],
        "simulated": True,
    }


@router.post("/recommendations/{recommendation_id}/approve")
async def approve_recommendation(
    recommendation_id: UUID,
    repository: RepositoryDep,
    actor: Annotated[str, Depends(require_operator_token)],
) -> dict[str, Any]:
    check_rate_limit(actor)
    return await _decide(recommendation_id, "approve", None, actor, repository)


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: UUID,
    payload: RejectRequest,
    repository: RepositoryDep,
    actor: Annotated[str, Depends(require_operator_token)],
) -> dict[str, Any]:
    check_rate_limit(actor)
    return await _decide(recommendation_id, "reject", payload.reason, actor, repository)
