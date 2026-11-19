"""Worker-only approval executor with fresh validation and stable-key retries."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from core.metrics import allocation_executor_failures, simulator_allocation_rejections
from core.models import Allocation, AllocationRequest, AllocationStatus, Snapshot
from core.sim_client import SimBusinessError, SimClient, SimInvalidResponse, SimUnavailable
from core.validator import validate

logger = logging.getLogger("fuel_simulator.worker.executor")


class ExecutorStore(Protocol):
    async def get_recommendations_for_execution(self) -> list[dict[str, Any]]: ...

    async def update_recommendation(
        self,
        recommendation_id: str,
        status: str,
        *,
        failure_reason: str | None = None,
        sim_allocation_id: int | None = None,
    ) -> None: ...


class Executor:
    def __init__(
        self,
        store: ExecutorStore,
        client: SimClient,
        fetch_snapshot: Callable[[], Awaitable[Snapshot]],
        *,
        poll_interval_s: float = 1.0,
    ) -> None:
        self.store = store
        self.client = client
        self.fetch_snapshot = fetch_snapshot
        self.poll_interval_s = max(0.1, poll_interval_s)

    async def run_once(self) -> None:
        rows = await self.store.get_recommendations_for_execution()
        for row in rows:
            if row["status"] not in {"APPROVED", "SUBMITTED", "IN_TRANSIT"}:
                continue
            try:
                snapshot = await self.fetch_snapshot()
            except Exception as exc:
                logger.warning(
                    json.dumps(
                        {
                            "event": "executor_fresh_read_failed",
                            "recommendation_id": str(row["id"]),
                            "error_type": type(exc).__name__,
                        }
                    )
                )
                continue
            if snapshot.stale or snapshot.data_status.value != "HEALTHY":
                await self.store.update_recommendation(
                    str(row["id"]),
                    "EXPIRED",
                    failure_reason="fresh simulator snapshot is stale or degraded",
                )
                continue

            stored_body = row["request_body"]
            if isinstance(stored_body, str):
                stored_body = json.loads(stored_body)
            try:
                request = AllocationRequest.model_validate(stored_body)
            except Exception as exc:
                await self.store.update_recommendation(
                    str(row["id"]),
                    "FAILED",
                    failure_reason=f"stored request is invalid: {type(exc).__name__}",
                )
                continue
            normalized_body = request.model_dump(mode="json")
            if request.idempotency_key != row["idempotency_key"] or normalized_body != stored_body:
                await self.store.update_recommendation(
                    str(row["id"]),
                    "FAILED",
                    failure_reason="stored idempotency key/body mismatch",
                )
                continue

            existing = next(
                (
                    allocation
                    for allocation in snapshot.allocations
                    if allocation.idempotency_key == request.idempotency_key
                ),
                None,
            )
            if existing is not None:
                replay_violations = validate(request, snapshot)
                if replay_violations:
                    await self.store.update_recommendation(
                        str(row["id"]),
                        "FAILED",
                        failure_reason=(
                            f"{replay_violations[0].code}: {replay_violations[0].message}"
                        ),
                    )
                    continue
                await self._record_allocation(row, existing)
                continue
            violations = validate(request, snapshot)
            if violations:
                await self.store.update_recommendation(
                    str(row["id"]),
                    "FAILED",
                    failure_reason=f"{violations[0].code}: {violations[0].message}",
                )
                continue

            await self.store.update_recommendation(str(row["id"]), "SUBMITTED")
            try:
                result = await self.client.create_allocation(normalized_body)
            except SimBusinessError as exc:
                if exc.status_code in (409, 422):
                    simulator_allocation_rejections.labels(code=exc.code).inc()
                await self.store.update_recommendation(
                    str(row["id"]),
                    "FAILED",
                    failure_reason=f"{exc.code}: {exc}",
                )
                continue
            except SimUnavailable as exc:
                # Keep SUBMITTED; the next loop reads fresh state and retries the exact body.
                logger.warning(
                    json.dumps(
                        {
                            "event": "allocation_submit_retry_pending",
                            "recommendation_id": str(row["id"]),
                            "error_type": type(exc).__name__,
                        }
                    )
                )
                continue
            except SimInvalidResponse as exc:
                await self.store.update_recommendation(
                    str(row["id"]),
                    "FAILED",
                    failure_reason=f"invalid simulator allocation response: {exc}",
                )
                continue
            await self._record_allocation(row, result.data)

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self.run_once()
            except Exception as exc:
                allocation_executor_failures.inc()
                logger.exception(
                    json.dumps(
                        {
                            "event": "allocation_executor_cycle_failed",
                            "error_type": type(exc).__name__,
                        }
                    )
                )
            try:
                await asyncio.wait_for(stop.wait(), timeout=self.poll_interval_s)
            except TimeoutError:
                pass

    async def _record_allocation(self, row: dict[str, Any], allocation: Allocation) -> None:
        status = {
            AllocationStatus.PENDING: "SUBMITTED",
            AllocationStatus.IN_TRANSIT: "IN_TRANSIT",
            AllocationStatus.ARRIVED: "ARRIVED",
            AllocationStatus.FAILED: "FAILED",
            AllocationStatus.CANCELLED: "FAILED",
        }[allocation.status]
        await self.store.update_recommendation(
            str(row["id"]),
            status,
            failure_reason=allocation.failure_reason,
            sim_allocation_id=allocation.id,
        )
        logger.info(
            json.dumps(
                {
                    "event": "allocation_recommendation_updated",
                    "recommendation_id": str(row["id"]),
                    "sim_allocation_id": allocation.id,
                    "status": status,
                }
            )
        )
