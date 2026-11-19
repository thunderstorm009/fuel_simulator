"""Database-only read repository for API routes."""

from __future__ import annotations

import json
from typing import Any, Protocol

import asyncpg


class ReadRepository(Protocol):
    async def get_latest_snapshot(self) -> dict[str, Any] | None: ...

    async def get_incidents(self) -> list[dict[str, Any]]: ...

    async def get_latest_forecasts(self) -> list[dict[str, Any]]: ...

    async def get_forecast_trajectory(
        self, station_id: str, fuel_type: str
    ) -> dict[str, Any] | None: ...

    async def get_recommendations(self) -> list[dict[str, Any]]: ...

    async def get_decisions(self) -> list[dict[str, Any]]: ...

    async def decide_recommendation(
        self, recommendation_id: str, action: str, reason: str | None, actor: str
    ) -> dict[str, Any] | None: ...


class PostgresReadRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @classmethod
    async def connect(cls, database_url: str) -> PostgresReadRepository:
        return cls(await asyncpg.create_pool(database_url, min_size=1, max_size=5))

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        row = await self.pool.fetchrow(
            """
            SELECT raw_json, fetched_at, stale, data_status
            FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1
            """
        )
        if row is None:
            return None
        raw_json = row["raw_json"]
        if isinstance(raw_json, str):
            raw_json = json.loads(raw_json)
        return {
            "raw_json": raw_json,
            "fetched_at": row["fetched_at"],
            "stale": row["stale"],
            "data_status": row["data_status"],
        }

    async def get_incidents(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT id, type, severity, detected_at, resolved_at, detail
            FROM incidents WHERE resolved_at IS NULL
            ORDER BY detected_at DESC LIMIT 100
            """
        )
        result = []
        for row in rows:
            item = dict(row)
            if isinstance(item.get("detail"), str):
                item["detail"] = json.loads(item["detail"])
            result.append(item)
        return result

    async def get_latest_forecasts(self) -> list[dict[str, Any]]:
        rows = await self.pool.fetch(
            """
            SELECT DISTINCT ON (station_id, fuel_type)
                station_id, fuel_type, tick, hours_to_stockout, p10, p50, p90,
                stockout_prob_24h, confidence, risk_level, needs_review, source, drivers
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
                return {
                    "recommendation": self._decode_recommendation(updated),
                    "decision_recorded": True,
                }

    @staticmethod
    def _decode_recommendation(row: Any) -> dict[str, Any]:
        result = dict(row)
        for column in ("request_body", "explanation_json"):
            if isinstance(result.get(column), str):
                result[column] = json.loads(result[column])
        return result

    @staticmethod
    def _decode_json_column(row: dict[str, Any], column: str) -> dict[str, Any]:
        value = row.get(column)
        if isinstance(value, str):
            row[column] = json.loads(value)
        return row

    async def close(self) -> None:
        await self.pool.close()
