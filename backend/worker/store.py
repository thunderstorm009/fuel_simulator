"""PostgreSQL persistence for worker-owned integration records."""

from __future__ import annotations

import json
from datetime import timezone
from typing import Any, Protocol

import asyncpg

from core.models import Snapshot
from core.risk import ForecastRecord


class SnapshotStore(Protocol):
    async def insert_snapshot(self, snapshot: Snapshot) -> bool: ...

    async def mark_latest_degraded(self) -> None: ...

    async def record_integration_event(self, kind: str, detail: dict[str, Any]) -> None: ...

    async def heartbeat(self, component: str, detail: dict[str, Any]) -> None: ...

    async def prune_snapshots(self, keep: int = 1000) -> None: ...


class PostgresStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @classmethod
    async def connect(cls, database_url: str) -> PostgresStore:
        pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
        await pool.execute("ALTER TABLE snapshots DROP CONSTRAINT IF EXISTS snapshots_tick_key")
        await pool.execute(
            "CREATE INDEX IF NOT EXISTS snapshots_tick_fetched_idx "
            "ON snapshots (tick, fetched_at DESC)"
        )
        await pool.execute(
            "ALTER TABLE forecasts ADD COLUMN IF NOT EXISTS trajectory "
            "JSONB NOT NULL DEFAULT '[]'::jsonb"
        )
        await pool.execute(
            "ALTER TABLE forecasts ADD COLUMN IF NOT EXISTS drivers "
            "JSONB NOT NULL DEFAULT '{}'::jsonb"
        )
        await pool.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS forecasts_snapshot_pair_idx "
            "ON forecasts (snapshot_id, station_id, fuel_type)"
        )
        await pool.execute(
            "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS failure_reason TEXT"
        )
        return cls(pool)

    async def insert_snapshot(self, snapshot: Snapshot) -> bool:
        payload = json.dumps(snapshot.model_dump(mode="json"), separators=(",", ":"))
        sim_time = snapshot.instance.sim_time
        if sim_time.tzinfo is None:
            sim_time = sim_time.replace(tzinfo=timezone.utc)
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                latest_tick = await connection.fetchval(
                    "SELECT tick FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1"
                )
                if latest_tick == snapshot.instance.tick:
                    await connection.execute(
                        """
                        UPDATE snapshots
                        SET fetched_at = $1, stale = $2, data_status = $3
                        WHERE id = (
                            SELECT id FROM snapshots
                            ORDER BY fetched_at DESC, id DESC LIMIT 1
                        )
                        """,
                        snapshot.fetched_at,
                        snapshot.stale,
                        snapshot.data_status.value,
                    )
                    return False
                await connection.execute(
                    """
                    INSERT INTO snapshots (tick, sim_time, raw_json, fetched_at, stale, data_status)
                    VALUES ($1, $2, $3::jsonb, $4, $5, $6)
                    """,
                    snapshot.instance.tick,
                    sim_time,
                    payload,
                    snapshot.fetched_at,
                    snapshot.stale,
                    snapshot.data_status.value,
                )
        return True

    async def mark_latest_degraded(self) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE snapshots SET data_status = 'DEGRADED'
                WHERE id = (
                    SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1
                )
                """
            )

    async def persist_forecasts(self, snapshot: Snapshot, records: list[ForecastRecord]) -> None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                snapshot_id = await connection.fetchval(
                    """
                    SELECT id FROM snapshots
                    WHERE tick = $1
                    ORDER BY fetched_at DESC, id DESC LIMIT 1
                    """,
                    snapshot.instance.tick,
                )
                if snapshot_id is None:
                    raise RuntimeError("cannot persist forecasts without a stored snapshot")
                for record in records:
                    forecast = record.forecast
                    previous_risk = await connection.fetchval(
                        """
                        SELECT risk_level FROM forecasts
                        WHERE station_id = $1 AND fuel_type = $2 AND snapshot_id < $3
                        ORDER BY snapshot_id DESC LIMIT 1
                        """,
                        forecast.station_id,
                        forecast.fuel_type.value,
                        snapshot_id,
                    )
                    await connection.execute(
                        """
                        INSERT INTO forecasts (
                            snapshot_id, tick, station_id, fuel_type, hours_to_stockout,
                            p10, p50, p90, stockout_prob_24h, confidence, risk_level,
                            needs_review, source, trajectory, drivers
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                            'local', $13::jsonb, $14::jsonb
                        )
                        ON CONFLICT (snapshot_id, station_id, fuel_type) DO UPDATE SET
                            hours_to_stockout = EXCLUDED.hours_to_stockout,
                            p10 = EXCLUDED.p10, p50 = EXCLUDED.p50, p90 = EXCLUDED.p90,
                            stockout_prob_24h = EXCLUDED.stockout_prob_24h,
                            confidence = EXCLUDED.confidence,
                            risk_level = EXCLUDED.risk_level,
                            needs_review = EXCLUDED.needs_review,
                            trajectory = EXCLUDED.trajectory,
                            drivers = EXCLUDED.drivers
                        """,
                        snapshot_id,
                        snapshot.instance.tick,
                        forecast.station_id,
                        forecast.fuel_type.value,
                        forecast.hours_to_stockout,
                        forecast.p10_hours,
                        forecast.p50_hours,
                        forecast.p90_hours,
                        forecast.stockout_probability_24h,
                        forecast.confidence,
                        forecast.risk_level.value,
                        forecast.needs_review,
                        json.dumps(
                            [point.__dict__ for point in record.trajectory],
                            separators=(",", ":"),
                        ),
                        json.dumps(record.drivers, separators=(",", ":")),
                    )
                    await self._update_risk_incident(
                        connection,
                        forecast.station_id,
                        forecast.fuel_type.value,
                        previous_risk,
                        forecast.risk_level.value,
                    )

    async def expire_stale_recommendations(self, tick: int) -> None:
        await self.pool.execute(
            """
            UPDATE recommendations
            SET status = 'EXPIRED', failure_reason = 'recommendation expired before review'
            WHERE status = 'PROPOSED' AND expires_tick < $1
            """,
            tick,
        )

    async def get_open_proposal_pairs(self) -> set[tuple[str, str]]:
        rows = await self.pool.fetch(
            """
            SELECT DISTINCT station_id, fuel_type FROM recommendations
            WHERE status IN ('PROPOSED', 'APPROVED', 'SUBMITTED', 'IN_TRANSIT')
            """
        )
        return {(row["station_id"], row["fuel_type"]) for row in rows}

    async def persist_recommendations(self, rows: list[dict[str, Any]]) -> None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                for row in rows:
                    await connection.execute(
                        """
                        INSERT INTO recommendations (
                            id, status, policy_used, fallback_used, depot_id, station_id,
                            route_id, fuel_type, quantity, idempotency_key, request_body,
                            explanation_json, created_tick, expires_tick, correlation_id,
                            sim_allocation_id, failure_reason
                        ) VALUES (
                            $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11::jsonb, $12::jsonb, $13, $14, $15, $16, $17
                        )
                        ON CONFLICT (idempotency_key) DO NOTHING
                        """,
                        row["id"],
                        row["status"],
                        row["policy_used"],
                        row["fallback_used"],
                        row["depot_id"],
                        row["station_id"],
                        row["route_id"],
                        row["fuel_type"],
                        row["quantity"],
                        row["idempotency_key"],
                        json.dumps(row["request_body"], separators=(",", ":")),
                        json.dumps(row["explanation_json"], separators=(",", ":")),
                        row["created_tick"],
                        row["expires_tick"],
                        row["correlation_id"],
                        row["sim_allocation_id"],
                        row["failure_reason"],
                    )

    async def get_recommendations_for_execution(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT * FROM recommendations
            WHERE status IN ('APPROVED', 'SUBMITTED', 'IN_TRANSIT')
            ORDER BY created_tick, id
            """
        )
        return [self._decode_recommendation(row) for row in rows]

    async def update_recommendation(
        self,
        recommendation_id: str,
        status: str,
        *,
        failure_reason: str | None = None,
        sim_allocation_id: int | None = None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE recommendations
            SET status = $2, failure_reason = $3,
                sim_allocation_id = COALESCE($4, sim_allocation_id)
            WHERE id = $1::uuid
            """,
            recommendation_id,
            status,
            failure_reason,
            sim_allocation_id,
        )

    @staticmethod
    def _decode_recommendation(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in ("request_body", "explanation_json"):
            if isinstance(result.get(field), str):
                result[field] = json.loads(result[field])
        return result

    @staticmethod
    async def _update_risk_incident(
        connection: asyncpg.Connection,
        station_id: str,
        fuel_type: str,
        previous_risk: str | None,
        current_risk: str,
    ) -> None:
        elevated = {"critical", "high"}
        active = current_risk in elevated
        previously_active = previous_risk in elevated if previous_risk else False
        if active:
            detail = json.dumps(
                {"station_id": station_id, "fuel_type": fuel_type, "risk_level": current_risk},
                separators=(",", ":"),
            )
            if previously_active:
                await connection.execute(
                    """
                    UPDATE incidents SET severity = $1, detail = $2::jsonb
                    WHERE type = 'stockout_risk' AND resolved_at IS NULL
                      AND detail->>'station_id' = $3 AND detail->>'fuel_type' = $4
                    """,
                    current_risk,
                    detail,
                    station_id,
                    fuel_type,
                )
            else:
                exists = await connection.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM incidents WHERE type = 'stockout_risk'
                        AND resolved_at IS NULL AND detail->>'station_id' = $1
                        AND detail->>'fuel_type' = $2
                    )
                    """,
                    station_id,
                    fuel_type,
                )
                if not exists:
                    await connection.execute(
                        """
                        INSERT INTO incidents (type, severity, detail)
                        VALUES ('stockout_risk', $1, $2::jsonb)
                        """,
                        current_risk,
                        detail,
                    )
        elif previously_active:
            await connection.execute(
                """
                UPDATE incidents SET resolved_at = now()
                WHERE type = 'stockout_risk' AND resolved_at IS NULL
                  AND detail->>'station_id' = $1 AND detail->>'fuel_type' = $2
                """,
                station_id,
                fuel_type,
            )

    async def record_integration_event(self, kind: str, detail: dict[str, Any]) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO integration_events (kind, detail) VALUES ($1, $2::jsonb)",
                kind,
                json.dumps(detail, separators=(",", ":")),
            )

    async def heartbeat(self, component: str, detail: dict[str, Any]) -> None:
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO heartbeats (component, last_seen, detail)
                VALUES ($1, now(), $2::jsonb)
                ON CONFLICT (component) DO UPDATE
                SET last_seen = EXCLUDED.last_seen, detail = EXCLUDED.detail
                """,
                component,
                json.dumps(detail, separators=(",", ":")),
            )

    async def prune_snapshots(self, keep: int = 1000) -> None:
        if keep < 1:
            raise ValueError("keep must be at least 1")
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM snapshots
                WHERE id NOT IN (
                    SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT $1
                )
                """,
                keep,
            )

    async def close(self) -> None:
        await self.pool.close()
