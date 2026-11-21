"""Run a bounded allocation policy and persist explainable proposals."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from math import ceil
from typing import Any, Protocol
from uuid import uuid4

from core.explain import build_explanation
from core.metrics import (
    policy_fallbacks,
    recommendation_fallbacks,
    recommendations_by_status,
    recommendations_created,
)
from core.models import AllocationRequest, Snapshot
from core.policies.base import Policy, PolicyPlan
from core.policies.heuristic import HeuristicPolicy
from core.risk import ForecastRecord

logger = logging.getLogger("fuel_simulator.worker.recommend")


class RecommendationStore(Protocol):
    async def expire_stale_recommendations(self, tick: int) -> None: ...

    async def get_open_proposal_pairs(self) -> set[tuple[str, str]]: ...

    async def persist_recommendations(self, rows: list[dict[str, Any]]) -> None: ...


class PolicyRunner:
    def __init__(
        self,
        primary: Policy,
        fallback: Policy | None = None,
        *,
        timeout_s: float = 0.5,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or HeuristicPolicy()
        self.timeout_s = max(0.01, timeout_s)

    async def recommend(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> tuple[list[PolicyPlan], bool, str]:
        try:
            plans = await asyncio.wait_for(
                asyncio.to_thread(self.primary.recommend, snapshot, forecasts),
                timeout=self.timeout_s,
            )
            return plans, False, self.primary.name
        except (Exception, TimeoutError):
            recommendation_fallbacks.inc()
            policy_fallbacks.labels(reason="recommendation_policy_failure").inc()
            logger.exception("primary allocation policy failed; using heuristic fallback")
            return (
                await asyncio.to_thread(self.fallback.recommend, snapshot, forecasts),
                True,
                self.fallback.name,
            )


class RecommendationJob:
    def __init__(
        self,
        store: RecommendationStore,
        *,
        primary: Policy | None = None,
        fallback: Policy | None = None,
        policy_timeout_s: float = 0.5,
        expiry_hours: float = 1.0,
        expiry_ticks: int = 0,
    ) -> None:
        self.store = store
        self.runner = PolicyRunner(
            primary or HeuristicPolicy(), fallback, timeout_s=policy_timeout_s
        )
        self.expiry_hours = max(0.25, expiry_hours)
        self.expiry_ticks = max(0, expiry_ticks)

    async def run(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> list[dict[str, Any]]:
        tick = snapshot.instance.tick
        await self.store.expire_stale_recommendations(tick)
        if snapshot.stale or snapshot.data_status.value != "HEALTHY":
            return []
        plans, fallback_used, policy_used = await self.runner.recommend(snapshot, forecasts)
        existing_pairs = await self.store.get_open_proposal_pairs()
        forecast_by_pair = {
            (record.forecast.station_id, record.forecast.fuel_type.value): record
            for record in forecasts
        }
        if self.expiry_ticks > 0:
            expire_after = self.expiry_ticks
        else:
            expire_after = max(1, ceil(self.expiry_hours * 60 / snapshot.instance.tick_minutes))
        rows: list[dict[str, Any]] = []
        for plan in plans:
            pair = (plan.request.destination_station_id, plan.request.fuel_type.value)
            if pair in existing_pairs:
                continue
            before = forecast_by_pair.get(pair)
            if before is None:
                continue
            recommendation_id = str(uuid4())
            idempotency_key = f"rec-{uuid4()}"
            body = AllocationRequest(
                idempotency_key=idempotency_key,
                **plan.request.model_dump(mode="json"),
            )
            row = {
                "id": recommendation_id,
                "status": "PROPOSED",
                "policy_used": policy_used,
                "fallback_used": fallback_used,
                "depot_id": body.source_depot_id,
                "station_id": body.destination_station_id,
                "route_id": body.route_id,
                "fuel_type": body.fuel_type.value,
                "quantity": body.quantity,
                "idempotency_key": body.idempotency_key,
                "request_body": body.model_dump(mode="json"),
                "explanation_json": build_explanation(
                    snapshot, plan, before, policy_used=policy_used
                ),
                "created_tick": tick,
                "expires_tick": tick + expire_after,
                "correlation_id": None,
                "sim_allocation_id": None,
                "failure_reason": None,
            }
            rows.append(row)
        if rows:
            await self.store.persist_recommendations(rows)
            recommendations_created.inc(len(rows))
            recommendations_by_status.labels(status="PROPOSED").inc(len(rows))
        return rows
