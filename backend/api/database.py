"""Database-only read repository for API routes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Protocol

import asyncpg

from core.metrics import active_policy, policy_changes_total
from core.models import Snapshot


class ReadRepository(Protocol):
    async def get_latest_snapshot(self) -> dict[str, Any] | None: ...

    async def get_latest_snapshot_meta(self) -> dict[str, Any] | None: ...

    async def get_latest_snapshot_model(self) -> Any: ...

    async def get_incidents(
        self, include_resolved: bool = False, limit: int = 100
    ) -> list[dict[str, Any]]: ...

    async def get_incident(self, incident_id: int) -> dict[str, Any] | None: ...

    async def get_depot_risks(self) -> list[dict[str, Any]]: ...

    async def get_tick_freshness(self) -> dict[str, float]: ...

    async def get_latest_forecasts(self) -> list[dict[str, Any]]: ...

    async def get_forecast_trajectory(
        self, station_id: str, fuel_type: str
    ) -> dict[str, Any] | None: ...

    async def get_recommendations(self) -> list[dict[str, Any]]: ...

    async def get_decisions(self) -> list[dict[str, Any]]: ...

    async def check_database(self) -> bool: ...

    async def get_heartbeat(self, component: str) -> dict[str, Any] | None: ...

    async def decide_recommendation(
        self, recommendation_id: str, action: str, reason: str | None, actor: str
    ) -> dict[str, Any] | None: ...

    async def get_active_policy(self) -> str: ...

    async def record_policy_change(
        self, policy: str, actor: str, reason: str
    ) -> dict[str, Any]: ...

    async def get_policy_history(self, limit: int = 50) -> list[dict[str, Any]]: ...


class PostgresReadRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self._cached_snapshot_id: int | None = None
        self._cached_snapshot_record: dict[str, Any] | None = None
        self._cached_snapshot_model: Snapshot | None = None

    @classmethod
    async def connect(cls, database_url: str) -> PostgresReadRepository:
        min_size = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
        max_size = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
        pool = await asyncpg.create_pool(database_url, min_size=min_size, max_size=max_size)
        await pool.execute(
            """
            ALTER TABLE forecasts
                ADD COLUMN IF NOT EXISTS model_version TEXT NOT NULL DEFAULT '1.1.0';
            ALTER TABLE recommendations
                ADD COLUMN IF NOT EXISTS model_version TEXT NOT NULL DEFAULT '1.1.0';
            ALTER TABLE recommendations
                ADD COLUMN IF NOT EXISTS policy_version TEXT NOT NULL DEFAULT '2.0.0';
            CREATE INDEX IF NOT EXISTS snapshots_fetched_id_idx
                ON snapshots (fetched_at DESC, id DESC);
            CREATE INDEX IF NOT EXISTS forecasts_pair_snapshot_idx
                ON forecasts (station_id, fuel_type, snapshot_id DESC);
            CREATE INDEX IF NOT EXISTS depot_risks_depot_snapshot_idx
                ON depot_risks (depot_id, fuel_type, snapshot_id DESC);
            CREATE TABLE IF NOT EXISTS policy_changes (
                id BIGSERIAL PRIMARY KEY,
                policy TEXT NOT NULL,
                previous_policy TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT NOT NULL,
                changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE INDEX IF NOT EXISTS policy_changes_changed_at_idx
                ON policy_changes (changed_at DESC);
            """
        )
        return cls(pool)

    async def get_latest_snapshot_meta(self) -> dict[str, Any] | None:
        row = await self.pool.fetchrow(
            """
            SELECT id, fetched_at, stale, data_status
            FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1
            """
        )
        if row is None:
            return None
        return dict(row)

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        meta = await self.get_latest_snapshot_meta()
        if meta is None:
            return None
        snap_id = meta["id"]
        if self._cached_snapshot_record is not None and self._cached_snapshot_id == snap_id:
            return self._cached_snapshot_record

        row = await self.pool.fetchrow(
            """
            SELECT id, raw_json, fetched_at, stale, data_status
            FROM snapshots WHERE id = $1
            """,
            snap_id,
        )
        if row is None:
            return None
        raw_json = row["raw_json"]
        if isinstance(raw_json, str):
            raw_json = json.loads(raw_json)
        record = {
            "id": row["id"],
            "raw_json": raw_json,
            "fetched_at": row["fetched_at"],
            "stale": row["stale"],
            "data_status": row["data_status"],
        }
        self._cached_snapshot_id = snap_id
        self._cached_snapshot_record = record
        try:
            self._cached_snapshot_model = Snapshot.model_validate(raw_json)
        except Exception:
            self._cached_snapshot_model = None
        return record

    async def get_latest_snapshot_model(self) -> Snapshot | None:
        await self.get_latest_snapshot()
        return self._cached_snapshot_model

    async def get_incidents(
        self, include_resolved: bool = False, limit: int = 100
    ) -> list[dict[str, Any]]:
        query = "SELECT id, type, severity, detected_at, resolved_at, detail FROM incidents"
        if not include_resolved:
            query += " WHERE resolved_at IS NULL"
        query += " ORDER BY detected_at DESC LIMIT $1"
        rows = await self.pool.fetch(query, max(1, limit))
        result = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("detail"), str):
                item["detail"] = json.loads(item["detail"])
            result.append(item)
        return result

    async def get_incident(self, incident_id: int) -> dict[str, Any] | None:
        query = (
            "SELECT id, type, severity, detected_at, resolved_at, detail "
            "FROM incidents WHERE id = $1"
        )
        row = await self.pool.fetchrow(query, incident_id)
        if not row:
            return None
        item = dict(row)
        if isinstance(item.get("detail"), str):
            item["detail"] = json.loads(item["detail"])
        return item

    async def get_depot_risks(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT depot_id, fuel_type, tick, current_inventory,
                scheduled_arrivals, committed_allocations, projected_demand,
                net_cover_liters, cover_hours, is_bottleneck, dispatch_utilization,
                evidence
            FROM depot_risks
            WHERE snapshot_id = (SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1)
            """
        )
        if not rows:
            rows = await self.pool.fetch(
                """
                SELECT DISTINCT ON (depot_id, fuel_type)
                    depot_id, fuel_type, tick, current_inventory,
                    scheduled_arrivals, committed_allocations, projected_demand,
                    net_cover_liters, cover_hours, is_bottleneck, dispatch_utilization,
                    evidence
                FROM depot_risks
                ORDER BY depot_id, fuel_type, snapshot_id DESC
                """
            )
        result = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("evidence"), str):
                item["evidence"] = json.loads(item["evidence"])
            result.append(item)
        return result

    async def get_tick_freshness(self) -> dict[str, float]:
        rows = await self.pool.fetch(
            """
            SELECT tick, fetched_at FROM snapshots
            ORDER BY fetched_at DESC, id DESC LIMIT 2
            """
        )
        if len(rows) < 2:
            return {"ticks_per_second": 0.0, "snapshot_age_ticks": 0.0}
        t1, t2 = rows[0]["tick"], rows[1]["tick"]
        f1, f2 = rows[0]["fetched_at"], rows[1]["fetched_at"]
        dt = (f1 - f2).total_seconds()
        tps = max(0.0, (t1 - t2) / max(0.001, dt)) if dt > 0 else 0.0
        age_seconds = max(0.0, (datetime.now(timezone.utc) - f1).total_seconds())
        age_ticks = round(age_seconds * tps, 1)
        return {"ticks_per_second": round(tps, 3), "snapshot_age_ticks": age_ticks}

    async def get_latest_forecasts(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT station_id, fuel_type, tick, hours_to_stockout, p10, p50, p90,
                stockout_prob_24h, confidence, risk_level, needs_review, source, drivers,
                model_version
            FROM forecasts
            WHERE snapshot_id = (SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1)
            """
        )
        if not rows:
            rows = await self.pool.fetch(
                """
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, tick, hours_to_stockout, p10, p50, p90,
                    stockout_prob_24h, confidence, risk_level, needs_review, source, drivers,
                    model_version
                FROM forecasts
                ORDER BY station_id, fuel_type, snapshot_id DESC
                """
            )
        return [self._decode_json_column(dict(row), "drivers") for row in rows]

    async def get_forecast_trajectory(
        self, station_id: str, fuel_type: str
    ) -> dict[str, Any] | None:
        row = await self.pool.fetchrow(
            """
            SELECT station_id, fuel_type, tick, hours_to_stockout, p10, p50, p90,
                stockout_prob_24h, confidence, risk_level, needs_review, source,
                trajectory, drivers
            FROM forecasts
            WHERE station_id = $1 AND fuel_type = $2
            ORDER BY snapshot_id DESC LIMIT 1
            """,
            station_id,
            fuel_type,
        )
        if row is None:
            return None
        result = dict(row)
        self._decode_json_column(result, "trajectory")
        self._decode_json_column(result, "drivers")
        return result

    async def get_recommendations(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT * FROM recommendations
            ORDER BY created_tick DESC, id DESC LIMIT 200
            """
        )
        return [self._decode_recommendation(row) for row in rows]

    async def get_decisions(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT d.id, d.recommendation_id, d.actor, d.action, d.reason, d.at,
                   r.status, r.station_id, r.fuel_type, r.quantity, r.route_id
            FROM decisions AS d
            JOIN recommendations AS r ON r.id = d.recommendation_id
            ORDER BY d.at DESC, d.id DESC LIMIT 200
            """
        )
        return [dict(row) for row in rows]

    async def check_database(self) -> bool:
        return int(await self.pool.fetchval("SELECT 1")) == 1

    async def get_heartbeat(self, component: str) -> dict[str, Any] | None:
        row = await self.pool.fetchrow(
            "SELECT component, last_seen, detail FROM heartbeats WHERE component = $1",
            component,
        )
        if row is None:
            return None
        result = dict(row)
        if isinstance(result.get("detail"), str):
            result["detail"] = json.loads(result["detail"])
        return result

    async def decide_recommendation(
        self, recommendation_id: str, action: str, reason: str | None, actor: str
    ) -> dict[str, Any] | None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    "SELECT * FROM recommendations WHERE id = $1::uuid FOR UPDATE",
                    recommendation_id,
                )
                if row is None:
                    return None
                recommendation = self._decode_recommendation(row)
                if action == "approve" and not self._request_matches_body(recommendation):
                    raise ValueError(
                        "stored recommendation fields do not match the allocation request"
                    )
                if recommendation["status"] == "APPROVED" and action == "approve":
                    return {"recommendation": recommendation, "decision_recorded": False}
                if recommendation["status"] != "PROPOSED":
                    raise ValueError("recommendation is not PROPOSED")
                latest_tick = await connection.fetchval(
                    "SELECT tick FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1"
                )
                if latest_tick is not None and recommendation["expires_tick"] < latest_tick:
                    await connection.execute(
                        """UPDATE recommendations SET status = 'EXPIRED',
                        failure_reason = 'recommendation expired before review'
                        WHERE id = $1::uuid""",
                        recommendation_id,
                    )
                    recommendation["status"] = "EXPIRED"
                    recommendation["failure_reason"] = "recommendation expired before review"
                    return {"recommendation": recommendation, "decision_recorded": False}
                new_status = "APPROVED" if action == "approve" else "REJECTED"
                updated = await connection.fetchrow(
                    """UPDATE recommendations SET status = $2 WHERE id = $1::uuid
                    RETURNING *""",
                    recommendation_id,
                    new_status,
                )
                await connection.execute(
                    """INSERT INTO decisions (recommendation_id, actor, action, reason)
                    VALUES ($1::uuid, $2, $3, $4)""",
                    recommendation_id,
                    actor,
                    action,
                    reason,
                )
                await connection.execute(
                    "SELECT pg_notify('platform_events', $1)",
                    json.dumps({"type": "recommendations"}),
                )
                return {
                    "recommendation": self._decode_recommendation(updated),
                    "decision_recorded": True,
                }

    async def get_active_policy(self) -> str:
        row = await self.pool.fetchrow("SELECT policy FROM policy_changes ORDER BY id DESC LIMIT 1")
        return str(row["policy"]) if row else "heuristic"

    async def record_policy_change(self, policy: str, actor: str, reason: str) -> dict[str, Any]:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                prev_row = await connection.fetchrow(
                    "SELECT policy FROM policy_changes ORDER BY id DESC LIMIT 1"
                )
                prev_policy = str(prev_row["policy"]) if prev_row else "heuristic"
                row = await connection.fetchrow(
                    """
                    INSERT INTO policy_changes (policy, previous_policy, actor, reason)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    """,
                    policy,
                    prev_policy,
                    actor,
                    reason,
                )
                await connection.execute(
                    "SELECT pg_notify('platform_events', $1)",
                    json.dumps({"type": "policy_change", "policy": policy}),
                )
        for p in ("heuristic", "heuristic_buffer", "optimizer"):
            active_policy.labels(policy=p).set(1.0 if p == policy else 0.0)
        policy_changes_total.labels(policy=policy, actor=actor).inc()
        return dict(row)

    async def get_policy_history(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            "SELECT * FROM policy_changes ORDER BY id DESC LIMIT $1", limit
        )
        return [dict(r) for r in rows]

    @staticmethod
    def _decode_recommendation(row: Any) -> dict[str, Any]:
        result = dict(row)
        for column in ("request_body", "explanation_json"):
            if isinstance(result.get(column), str):
                result[column] = json.loads(result[column])
        return result

    @staticmethod
    def _request_matches_body(recommendation: dict[str, Any]) -> bool:
        body = recommendation.get("request_body")
        if not isinstance(body, dict):
            return False
        return all(
            recommendation.get(column) == body.get(request_field)
            for column, request_field in (
                ("depot_id", "source_depot_id"),
                ("station_id", "destination_station_id"),
                ("route_id", "route_id"),
                ("fuel_type", "fuel_type"),
                ("quantity", "quantity"),
                ("idempotency_key", "idempotency_key"),
            )
        )

    @staticmethod
    def _decode_json_column(row: dict[str, Any], column: str) -> dict[str, Any]:
        value = row.get(column)
        if isinstance(value, str):
            row[column] = json.loads(value)
        return row

    async def close(self) -> None:
        await self.pool.close()
