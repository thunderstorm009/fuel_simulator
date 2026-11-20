from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

import pytest
from api.database import PostgresReadRepository


def test_database_mapping_keeps_similar_recommendations_bound_to_their_own_body() -> None:
    large_body = {
        "source_depot_id": "depot-patiya",
        "destination_station_id": "station-coxsbazar",
        "route_id": "route-patiya-coxsbazar",
        "fuel_type": "DIESEL",
        "quantity": 6000.0,
        "idempotency_key": "rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a",
    }
    smaller_body = {
        **large_body,
        "quantity": 1543.5502472239223,
        "idempotency_key": "rec-9a2da662-644a-4256-ab25-41695ffb753e",
    }
    rows = [
        {
            "id": "1cb05b67-3440-45e5-a6d8-398482678d8c",
            "depot_id": "depot-patiya",
            "station_id": "station-coxsbazar",
            "route_id": "route-patiya-coxsbazar",
            "fuel_type": "DIESEL",
            "quantity": large_body["quantity"],
            "idempotency_key": large_body["idempotency_key"],
            "request_body": json.dumps(large_body),
            "explanation_json": "{}",
        },
        {
            "id": "dab6db72-4f94-4b09-a167-d1dea8c1f2fc",
            "depot_id": "depot-patiya",
            "station_id": "station-coxsbazar",
            "route_id": "route-patiya-coxsbazar",
            "fuel_type": "DIESEL",
            "quantity": smaller_body["quantity"],
            "idempotency_key": smaller_body["idempotency_key"],
            "request_body": json.dumps(smaller_body),
            "explanation_json": "{}",
        },
    ]

    mapped = [PostgresReadRepository._decode_recommendation(row) for row in rows]

    assert [(row["id"], row["quantity"], row["request_body"]["quantity"]) for row in mapped] == [
        ("1cb05b67-3440-45e5-a6d8-398482678d8c", 6000.0, 6000.0),
        (
            "dab6db72-4f94-4b09-a167-d1dea8c1f2fc",
            1543.5502472239223,
            1543.5502472239223,
        ),
    ]
    assert [row["request_body"]["idempotency_key"] for row in mapped] == [
        "rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a",
        "rec-9a2da662-644a-4256-ab25-41695ffb753e",
    ]
    assert all(PostgresReadRepository._request_matches_body(row) for row in mapped)


def test_database_mapping_detects_request_body_quantity_or_key_mismatch() -> None:
    recommendation = {
        "depot_id": "depot-patiya",
        "station_id": "station-coxsbazar",
        "route_id": "route-patiya-coxsbazar",
        "fuel_type": "DIESEL",
        "quantity": 6000.0,
        "idempotency_key": "rec-exact-key",
        "request_body": {
            "source_depot_id": "depot-patiya",
            "destination_station_id": "station-coxsbazar",
            "route_id": "route-patiya-coxsbazar",
            "fuel_type": "DIESEL",
            "quantity": 1543.5502472239223,
            "idempotency_key": "rec-other-key",
        },
    }

    assert PostgresReadRepository._request_matches_body(recommendation) is False


class DecisionConnection:
    def __init__(self, row: dict[str, Any]) -> None:
        self.row = row
        self.writes: list[str] = []

    @asynccontextmanager
    async def transaction(self):
        yield

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any]:
        return self.row

    async def execute(self, query: str, *args: Any) -> None:
        self.writes.append(query)


class DecisionPool:
    def __init__(self, connection: DecisionConnection) -> None:
        self.connection = connection

    @asynccontextmanager
    async def acquire(self):
        yield self.connection


@pytest.mark.asyncio
async def test_approval_fails_closed_without_writing_a_decision_when_body_differs() -> None:
    row = {
        "id": "1cb05b67-3440-45e5-a6d8-398482678d8c",
        "status": "PROPOSED",
        "depot_id": "depot-patiya",
        "station_id": "station-coxsbazar",
        "route_id": "route-patiya-coxsbazar",
        "fuel_type": "DIESEL",
        "quantity": 6000.0,
        "idempotency_key": "rec-exact-key",
        "request_body": {
            "source_depot_id": "depot-patiya",
            "destination_station_id": "station-coxsbazar",
            "route_id": "route-patiya-coxsbazar",
            "fuel_type": "DIESEL",
            "quantity": 1543.5502472239223,
            "idempotency_key": "rec-other-key",
        },
    }
    connection = DecisionConnection(row)
    repository = PostgresReadRepository(DecisionPool(connection))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="do not match"):
        await repository.decide_recommendation(row["id"], "approve", None, "operator")

    assert connection.writes == []
