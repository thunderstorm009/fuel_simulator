from __future__ import annotations

from typing import Any

import pytest
from api.main import app
from api.routes.read import get_repository
from fastapi.testclient import TestClient


class FakeRecommendationRepository:
    def __init__(self) -> None:
        self.rows = {
            "123e4567-e89b-12d3-a456-426614174000": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "PROPOSED",
                "station_id": "station-mirpur",
                "fuel_type": "DIESEL",
                "quantity": 3000,
                "request_body": {"idempotency_key": "rec-test"},
                "explanation_json": {"risk_before": {"risk_level": "critical"}},
            }
        }
        self.decisions: list[dict[str, Any]] = []

    async def get_recommendations(self) -> list[dict[str, Any]]:
        return list(self.rows.values())

    async def get_decisions(self) -> list[dict[str, Any]]:
        return self.decisions

    async def decide_recommendation(
        self, recommendation_id: str, action: str, reason: str | None, actor: str
    ) -> dict[str, Any] | None:
        row = self.rows.get(recommendation_id)
        if row is None:
            return None
        if row["status"] == "APPROVED" and action == "approve":
            return {"recommendation": row, "decision_recorded": False}
        if row["status"] != "PROPOSED":
            raise ValueError("recommendation is not PROPOSED")
        row["status"] = "APPROVED" if action == "approve" else "REJECTED"
        decision = {
            "recommendation_id": recommendation_id,
            "action": action,
            "reason": reason,
            "actor": actor,
        }
        self.decisions.append(decision)
        return {"recommendation": row, "decision_recorded": True}


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch):
    repository = FakeRecommendationRepository()
    app.dependency_overrides[get_repository] = lambda: repository
    monkeypatch.setenv("OPERATOR_TOKEN", "test-token")
    try:
        with TestClient(app) as client:
            yield client, repository
    finally:
        app.dependency_overrides.clear()


def test_recommendation_and_decision_reads_are_database_backed(api_client) -> None:
    client, repository = api_client
    del repository

    assert client.get("/api/recommendations").json()["recommendations"][0]["status"] == "PROPOSED"
    assert client.get("/api/decisions").json() == {"decisions": [], "simulated": True}


def test_approval_requires_token_and_double_approval_is_idempotent(api_client) -> None:
    client, repository = api_client
    path = "/api/recommendations/123e4567-e89b-12d3-a456-426614174000/approve"

    assert client.post(path).status_code == 401
    first = client.post(path, headers={"X-Operator-Token": "test-token"})
    second = client.post(path, headers={"X-Operator-Token": "test-token"})

    assert first.status_code == 200
    assert first.json()["status"] == "APPROVED"
    assert second.status_code == 200
    assert second.json()["already_decided"] is True
    assert len(repository.decisions) == 1


def test_rejection_requires_reason_and_records_decision(api_client) -> None:
    client, repository = api_client
    path = "/api/recommendations/123e4567-e89b-12d3-a456-426614174000/reject"
    headers = {"X-Operator-Token": "test-token"}

    assert client.post(path, headers=headers).status_code == 422
    assert client.post(path, headers=headers, json={"reason": "   "}).status_code == 422
    response = client.post(path, headers=headers, json={"reason": "quantities are too high"})

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    assert repository.decisions[0]["reason"] == "quantities are too high"
