"""Run a bounded allocation policy and persist explainable proposals."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
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
from core.models import AllocationRequest, AllocationTerms, Snapshot
from core.policies.base import Policy, PolicyPlan
from core.policies.heuristic import HeuristicPolicy
from core.policies.optimizer import OptimizerPolicy
from core.risk import ForecastRecord
from core.validator import validate
from core.version import MODEL_VERSION, POLICY_VERSION

logger = logging.getLogger("fuel_simulator.worker.recommend")

RollbackCallback = Callable[[str, str, list[str]], Awaitable[None]]


def resolve_policy(name: str) -> Policy:
    if name == "heuristic_buffer":
        return HeuristicPolicy(enable_uncertainty_buffer=True, name="heuristic_buffer")
    if name == "optimizer":
        return OptimizerPolicy()
    return HeuristicPolicy(enable_uncertainty_buffer=False, name="heuristic")


class RecommendationStore(Protocol):
    async def expire_stale_recommendations(self, tick: int) -> None: ...

    async def get_open_proposal_pairs(self) -> set[tuple[str, str]]: ...

    async def persist_recommendations(self, rows: list[dict[str, Any]]) -> None: ...

    async def get_active_policy(self) -> str: ...

    async def record_policy_rollback(
        self, failed_policy: str, reason: str, violations: list[str]
    ) -> None: ...


class PolicyRunner:
    def __init__(
        self,
        primary: Policy,
        fallback: Policy | None = None,
        *,
        timeout_s: float = 0.5,
        on_rollback: RollbackCallback | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or HeuristicPolicy(enable_uncertainty_buffer=False)
        self.timeout_s = max(0.01, timeout_s)
        self.on_rollback = on_rollback

    async def recommend(
        self, snapshot: Snapshot, forecasts: Sequence[ForecastRecord]
    ) -> tuple[list[PolicyPlan], bool, str]:
        if self.primary.name == self.fallback.name:
            plans = await asyncio.to_thread(self.fallback.recommend, snapshot, forecasts)
            return plans, False, self.fallback.name

        failed = False
        reason = ""
        violations: list[str] = []
        plans: list[PolicyPlan] = []

        try:
            plans = await asyncio.wait_for(
                asyncio.to_thread(self.primary.recommend, snapshot, forecasts),
                timeout=self.timeout_s,
            )
            # Validate every emitted candidate plan
            step_reservations: list[AllocationTerms] = []
            for p in plans:
                v = validate(p.request, snapshot, step_reservations)
                if v:
                    violations.extend([f"{err.code}: {err.message}" for err in v])
                    failed = True
                    reason = f"validator violation: {violations[0]}"
                    break
                step_reservations.append(p.request)
        except asyncio.TimeoutError:
            failed = True
            reason = f"policy {self.primary.name} execution timed out ({self.timeout_s}s)"
        except Exception as exc:
            failed = True
            reason = f"policy {self.primary.name} exception: {exc}"

        if failed:
            recommendation_fallbacks.inc()
            policy_fallbacks.labels(reason="recommendation_policy_failure").inc()
            failed_name = self.primary.name
            logger.warning(
                "Policy %s failed (%s); rolling back to %s",
                failed_name,
                reason,
                self.fallback.name,
            )
            self.primary = self.fallback
            if self.on_rollback:
                try:
                    await self.on_rollback(failed_name, reason, violations)
                except Exception as err:
                    logger.exception("Failed to record policy rollback: %s", err)
            fallback_plans = await asyncio.to_thread(self.fallback.recommend, snapshot, forecasts)
            valid_fallback_plans: list[PolicyPlan] = []
            fb_reservations: list[AllocationTerms] = []
            for p in fallback_plans:
                if not validate(p.request, snapshot, fb_reservations):
                    valid_fallback_plans.append(p)
                    fb_reservations.append(p.request)
            return valid_fallback_plans, True, self.fallback.name

        return plans, False, self.primary.name


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
            primary or HeuristicPolicy(enable_uncertainty_buffer=False),
            fallback,
            timeout_s=policy_timeout_s,
            on_rollback=getattr(store, "record_policy_rollback", None),
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
        if hasattr(self.store, "get_active_policy"):
            active_name = await self.store.get_active_policy()
            if self.runner.primary.name != active_name:
                self.runner.primary = resolve_policy(active_name)
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
                "model_version": MODEL_VERSION,
                "policy_version": POLICY_VERSION,
            }
            rows.append(row)
        if rows:
            await self.store.persist_recommendations(rows)
            recommendations_created.inc(len(rows))
            recommendations_by_status.labels(status="PROPOSED").inc(len(rows))
        return rows
