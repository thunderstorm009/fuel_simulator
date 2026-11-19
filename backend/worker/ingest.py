"""Atomic simulator snapshot collection and persistence."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Callable

from core.metrics import (
    forecast_job_failures,
    snapshot_age,
    snapshot_rejected,
    worker_ingest_failures,
    worker_ingest_success,
)
from core.models import DataStatus, Snapshot
from core.sim_client import BreakerState, SimClient
from worker.store import SnapshotStore

logger = logging.getLogger("fuel_simulator.worker.ingest")


def derive_data_status(age_seconds: float, stale: bool, breaker_state: BreakerState) -> DataStatus:
    if age_seconds > 120:
        return DataStatus.OFFLINE
    if stale or breaker_state in (BreakerState.OPEN, BreakerState.HALF_OPEN) or age_seconds >= 15:
        return DataStatus.DEGRADED
    return DataStatus.HEALTHY


class SnapshotIngestor:
    def __init__(
        self,
        client: SimClient,
        store: SnapshotStore,
        *,
        now: Callable[[], datetime] | None = None,
        demand_limit: int = 100,
        keep_snapshots: int = 1000,
        on_snapshot: Callable[[Snapshot], Awaitable[None]] | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.demand_limit = demand_limit
        self.keep_snapshots = keep_snapshots
        self.on_snapshot = on_snapshot

    async def fetch_snapshot(self) -> Snapshot:
        results = await asyncio.gather(
            self.client.get_instance(),
            self.client.get_regions(),
            self.client.get_depots(),
            self.client.get_stations(),
            self.client.get_routes(),
            self.client.get_supply_arrivals(),
            self.client.get_events(),
            self.client.get_allocations(),
            self.client.get_metrics(),
        )
        (
            instance,
            regions,
            depots,
            stations,
            routes,
            supply_arrivals,
            events,
            allocations,
            metrics,
        ) = results
        station_rows = stations.data
        histories = await asyncio.gather(
            *(
                self.client.get_demand_history(station.id, limit=self.demand_limit)
                for station in station_rows
            )
        )
        fetched_at = self._now()
        stale = any(result.stale for result in results) or any(result.stale for result in histories)
        data_status = derive_data_status(0.0, stale, self.client.breaker.state)
        return Snapshot(
            instance=instance.data,
            regions=regions.data,
            depots=depots.data,
            stations=station_rows,
            routes=routes.data,
            supply_arrivals=supply_arrivals.data,
            events=events.data,
            allocations=allocations.data,
            demand_history=[row for result in histories for row in result.data],
            metrics=metrics.data,
            fetched_at=fetched_at,
            stale=stale,
            data_status=data_status,
        )

    async def run_once(self) -> bool:
        try:
            snapshot = await self.fetch_snapshot()
            inserted = await self.store.insert_snapshot(snapshot)
            if self.on_snapshot is not None:
                try:
                    await self.on_snapshot(snapshot)
                except Exception as forecast_exc:
                    forecast_job_failures.inc()
                    logger.exception(
                        json.dumps(
                            {
                                "event": "forecast_job_failed",
                                "error_type": type(forecast_exc).__name__,
                            }
                        )
                    )
                    try:
                        await self.store.record_integration_event(
                            "forecast_job_failed",
                            {"error_type": type(forecast_exc).__name__},
                        )
                    except Exception:
                        logger.exception(
                            json.dumps({"event": "forecast_failure_event_write_failed"})
                        )
            await self.store.heartbeat(
                "worker",
                {
                    "tick": snapshot.instance.tick,
                    "data_status": snapshot.data_status.value,
                    "breaker_state": self.client.breaker.state.value,
                },
            )
            await self.store.prune_snapshots(self.keep_snapshots)
            snapshot_age.set(max(0.0, (self._now() - snapshot.fetched_at).total_seconds()))
            worker_ingest_success.inc()
            logger.info(
                json.dumps(
                    {
                        "event": "snapshot_ingested" if inserted else "snapshot_unchanged",
                        "tick": snapshot.instance.tick,
                        "data_status": snapshot.data_status.value,
                    }
                )
            )
            return inserted
        except Exception as exc:
            worker_ingest_failures.inc()
            reason = type(exc).__name__
            snapshot_rejected.labels(reason=reason).inc()
            event = {
                "error_type": reason,
                "message": str(exc),
            }
            logger.warning(json.dumps({"event": "snapshot_rejected", **event}))
            try:
                await self.store.mark_latest_degraded()
            except Exception as store_exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "snapshot_status_update_failed",
                            "error_type": type(store_exc).__name__,
                        }
                    )
                )
            try:
                await self.store.record_integration_event("snapshot_rejected", event)
            except Exception as store_exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "integration_event_write_failed",
                            "error_type": type(store_exc).__name__,
                        }
                    )
                )
            try:
                await self.store.heartbeat(
                    "worker",
                    {"last_ingest_ok": False, "last_error_type": reason},
                )
            except Exception as store_exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "worker_heartbeat_write_failed",
                            "error_type": type(store_exc).__name__,
                        }
                    )
                )
            return False
