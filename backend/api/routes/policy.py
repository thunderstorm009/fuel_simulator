from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from api.database import ReadRepository

router = APIRouter(prefix="/api", tags=["policy"])

# Sliding window rate limiter for policy switch actions
_POLICY_SWITCH_CALLS: defaultdict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW_SECONDS: float = 60.0


def check_policy_rate_limit(key: str = "operator") -> None:
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    calls = [t for t in _POLICY_SWITCH_CALLS[key] if t > window_start]
    _POLICY_SWITCH_CALLS[key] = calls
    limit = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
    workers = max(1, int(os.getenv("API_WORKERS", "1")))
    max_reqs = max(5, limit // workers)
    if len(calls) >= max_reqs:
        raise HTTPException(
            status_code=429,
            detail=f"Too Many Requests: Policy rate limit exceeded. Max {max_reqs}/min.",
        )
    _POLICY_SWITCH_CALLS[key].append(now)


def get_repository(request: Request) -> ReadRepository:
    repository = getattr(request.app.state, "repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail="No snapshot repository is available")
    return repository


RepositoryDep = Annotated[ReadRepository, Depends(get_repository)]


def require_operator_token(
    token: Annotated[str, Header(alias="X-Operator-Token")] = "",
) -> str:
    expected = os.getenv("OPERATOR_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="Operator decisions are not configured")
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid operator token")
    return "operator"


OperatorDep = Annotated[str, Depends(require_operator_token)]


class PolicySwitchRequest(BaseModel):
    policy: Literal["heuristic", "heuristic_buffer", "optimizer"]
    reason: str = Field(min_length=1, max_length=500)
    actor: str = "operator"

    @field_validator("reason")
    @classmethod
    def reason_must_contain_non_whitespace(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must contain non-whitespace text")
        return normalized


@router.get("/policy")
async def get_policy(repository: RepositoryDep) -> dict[str, Any]:
    active = await repository.get_active_policy()
    history = await repository.get_policy_history()
    return {
        "active_policy": active,
        "history": history,
        "simulated": True,
    }


@router.post("/policy")
async def switch_policy(
    payload: PolicySwitchRequest,
    repository: RepositoryDep,
    _actor: OperatorDep,
) -> dict[str, Any]:
    check_policy_rate_limit("policy_switch")
    row = await repository.record_policy_change(
        policy=payload.policy,
        actor=payload.actor,
        reason=payload.reason,
    )
    ts = row["changed_at"]
    changed_at = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
    return {
        "status": "switched",
        "policy": row["policy"],
        "previous_policy": row["previous_policy"],
        "actor": row["actor"],
        "reason": row["reason"],
        "changed_at": changed_at,
        "simulated": True,
    }
