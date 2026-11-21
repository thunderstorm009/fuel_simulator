"""PostgreSQL persistence for worker-owned integration records."""

from __future__ import annotations

import json
from datetime import timezone
from typing import Any, Protocol

import asyncpg

from core.depot_risk import DepotRiskProjection
from core.detect import IncidentDetection
from core.metrics import alerts_active, detections_total, recommendations_by_status
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
        await pool.execute(
            """
            CREATE TABLE IF NOT EXISTS depot_risks (
                id BIGSERIAL PRIMARY KEY,
                snapshot_id BIGINT NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                tick INTEGER NOT NULL,
                depot_id TEXT NOT NULL,
                fuel_type TEXT NOT NULL CHECK (fuel_type IN ('DIESEL', 'PETROL', 'OCTANE')),
                current_inventory DOUBLE PRECISION NOT NULL,
                scheduled_arrivals DOUBLE PRECISION NOT NULL,
                committed_allocations DOUBLE PRECISION NOT NULL,
                projected_demand DOUBLE PRECISION NOT NULL,
                net_cover_liters DOUBLE PRECISION NOT NULL,
                cover_hours DOUBLE PRECISION NOT NULL,
                is_bottleneck BOOLEAN NOT NULL DEFAULT FALSE,
                dispatch_utilization DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                evidence JSONB NOT NULL DEFAULT '{}'::jsonb
            );
            CREATE INDEX IF NOT EXISTS depot_risks_depot_tick_idx
                ON depot_risks (depot_id, fuel_type, tick DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS depot_risks_snapshot_pair_idx
                ON depot_risks (snapshot_id, depot_id, fuel_type);
            CREATE INDEX IF NOT EXISTS incidents_dedup_idx
                ON incidents (type, (detail->>'dedup_key')) WHERE resolved_at IS NULL;
            """
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
                        SET sim_time = $1, raw_json = $2::jsonb, fetched_at = $3,
                            stale = $4, data_status = $5
                        WHERE id = (
                            SELECT id FROM snapshots
                            ORDER BY fetched_at DESC, id DESC LIMIT 1
                        )
                        """,
                        sim_time,
                        payload,
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
                            $13, $14::jsonb, $15::jsonb
                        )
                        ON CONFLICT (snapshot_id, station_id, fuel_type) DO UPDATE SET
                            hours_to_stockout = EXCLUDED.hours_to_stockout,
                            p10 = EXCLUDED.p10, p50 = EXCLUDED.p50, p90 = EXCLUDED.p90,
                            stockout_prob_24h = EXCLUDED.stockout_prob_24h,
                            confidence = EXCLUDED.confidence,
                            risk_level = EXCLUDED.risk_level,
                            needs_review = EXCLUDED.needs_review,
                            source = EXCLUDED.source,
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
                        record.source,
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
                await self._refresh_active_alert_metrics(connection)

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
        recommendations_by_status.labels(status=status).inc()

    async def set_predictor_incident(self, active: bool, reason: str | None = None) -> None:
        async with self.pool.acquire() as connection:
            if active:
                detail = json.dumps({"reason": reason or "unavailable"}, separators=(",", ":"))
                await connection.execute(
                    """
                    INSERT INTO incidents (type, severity, detail)
                    SELECT 'predictor_fallback', 'high', $1::jsonb
                    WHERE NOT EXISTS (
                        SELECT 1 FROM incidents
                        WHERE type = 'predictor_fallback' AND resolved_at IS NULL
                    )
                    """,
                    detail,
                )
            else:
                await connection.execute(
                    """UPDATE incidents SET resolved_at = now()
                    WHERE type = 'predictor_fallback' AND resolved_at IS NULL"""
                )
            await self._refresh_active_alert_metrics(connection)

    async def persist_depot_risks(
        self, snapshot: Snapshot, risks: list[DepotRiskProjection]
    ) -> None:
        if not risks:
            return
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
                    return
                for risk in risks:
                    await connection.execute(
                        """
                        INSERT INTO depot_risks (
                            snapshot_id, tick, depot_id, fuel_type,
                            current_inventory, scheduled_arrivals, committed_allocations,
                            projected_demand, net_cover_liters, cover_hours,
                            is_bottleneck, dispatch_utilization, evidence
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb)
                        ON CONFLICT (snapshot_id, depot_id, fuel_type) DO UPDATE SET
                            current_inventory = EXCLUDED.current_inventory,
                            scheduled_arrivals = EXCLUDED.scheduled_arrivals,
                            committed_allocations = EXCLUDED.committed_allocations,
                            projected_demand = EXCLUDED.projected_demand,
                            net_cover_liters = EXCLUDED.net_cover_liters,
                            cover_hours = EXCLUDED.cover_hours,
                            is_bottleneck = EXCLUDED.is_bottleneck,
                            dispatch_utilization = EXCLUDED.dispatch_utilization,
                            evidence = EXCLUDED.evidence
                        """,
                        snapshot_id,
                        snapshot.instance.tick,
                        risk.depot_id,
                        risk.fuel_type,
                        risk.current_inventory,
                        risk.scheduled_arrivals,
                        risk.committed_allocations,
                        risk.projected_demand,
                        risk.net_cover_liters,
                        risk.cover_hours,
                        risk.is_bottleneck,
                        risk.dispatch_utilization,
                        json.dumps(risk.evidence, separators=(",", ":")),
                    )

    async def sync_detections(self, detections: list[IncidentDetection]) -> None:
        detector_types = [
            "demand_anomaly",
            "regional_surge",
            "abnormal_inventory",
            "bottleneck",
            "emerging_regional_disruption",
        ]
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                open_rows = await connection.fetch(
                    """
                    SELECT id, type, severity, detail->>'dedup_key' AS dedup_key
                    FROM incidents
                    WHERE resolved_at IS NULL AND type = ANY($1::text[])
                    """,
                    detector_types,
                )
                open_by_key = {row["dedup_key"]: row for row in open_rows if row["dedup_key"]}
                active_by_key = {d.dedup_key: d for d in detections}

                # Resolve cleared incidents
                for dedup_key, row in open_by_key.items():
                    if dedup_key not in active_by_key:
                        await connection.execute(
                            "UPDATE incidents SET resolved_at = now() WHERE id = $1",
                            row["id"],
                        )

                # Insert or update active detections
                for d in detections:
                    detail_json = json.dumps(
                        {
                            "dedup_key": d.dedup_key,
                            "entity_id": d.entity_id,
                            "explanation": d.explanation,
                            "recovery_condition": d.recovery_condition,
                            "evidence": d.evidence,
                        },
                        separators=(",", ":"),
                    )
                    existing = open_by_key.get(d.dedup_key)
                    if existing is not None:
                        await connection.execute(
                            """
                            UPDATE incidents
                            SET severity = $1, detail = $2::jsonb
                            WHERE id = $3
                            """,
                            d.severity.lower(),
                            detail_json,
                            existing["id"],
                        )
                    else:
                        await connection.execute(
                            """
                            INSERT INTO incidents (type, severity, detail)
                            VALUES ($1, $2, $3::jsonb)
                            """,
                            d.type,
                            d.severity.lower(),
                            detail_json,
                        )
                        detections_total.labels(type=d.type).inc()

            await self._refresh_active_alert_metrics(connection)

    @staticmethod
    async def _refresh_active_alert_metrics(connection: asyncpg.Connection) -> None:
        rows = await connection.fetch(
            """SELECT LOWER(severity) AS severity, COUNT(*) AS count FROM incidents
            WHERE resolved_at IS NULL GROUP BY LOWER(severity)"""
        )
        counts = {str(row["severity"]): int(row["count"]) for row in rows}
        if "warning" in counts:
            counts["high"] = counts.get("high", 0) + counts.pop("warning")
        if "info" in counts:
            counts["low"] = counts.get("low", 0) + counts.pop("info")
        for severity in ("critical", "high", "medium", "low"):
            alerts_active.labels(severity=severity).set(counts.get(severity, 0))

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
