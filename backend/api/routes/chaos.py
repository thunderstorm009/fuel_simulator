"""Operator-protected demo fault controls; these do not call simulator endpoints."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.routes.recommendations import require_operator_token

router = APIRouter(prefix="/api")


class ForecastFailureRequest(BaseModel):
    enabled: bool


@router.post("/chaos/forecast-fail")
async def forecast_failure(
    payload: ForecastFailureRequest,
    _: str = Depends(require_operator_token),
) -> dict[str, Any]:
    predictor_url = os.getenv("PREDICTOR_URL", "http://predictor:8103").rstrip("/")
    token = os.getenv("OPERATOR_TOKEN", "")
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{predictor_url}/chaos/fail",
                json=payload.model_dump(),
                headers={"X-Operator-Token": token},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503, detail="Predictor fault control is unavailable"
        ) from exc
    if response.status_code == 401:
        raise HTTPException(status_code=503, detail="Predictor fault control is not configured")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Predictor fault control failed")
    return {"enabled": payload.enabled, "simulated": True}
