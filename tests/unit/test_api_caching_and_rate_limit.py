from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from api.main import app
from api.routes.read import clear_response_cache, get_repository
from api.routes.recommendations import (
    _DECISION_CALLS,
    check_rate_limit,
    get_rate_limit_max_requests,
)
from fastapi.testclient import TestClient

SAMPLES = Path(__file__).parents[2] / "docs" / "sim-samples"


class MockSnapshotRepo:
    def __init__(self, snapshot_id: int = 100) -> None:
        self.snapshot_id = snapshot_id
        raw = {
            "instance": json.loads((SAMPLES / "instance.json").read_text()),
            "regions": json.loads((SAMPLES / "regions.json").read_text()),
            "depots": json.loads((SAMPLES / "depots.json").read_text()),
            "stations": json.loads((SAMPLES / "stations.json").read_text()),
            "routes": json.loads((SAMPLES / "routes.json").read_text()),
            "supply_arrivals": json.loads((SAMPLES / "supply-arrivals.json").read_text()),
            "events": json.loads((SAMPLES / "events.json").read_text()),
            "allocations": json.loads((SAMPLES / "allocations.json").read_text()),
            "demand_history": [],
            "metrics": json.loads((SAMPLES / "metrics.json").read_text()),
            "stale": False,
            "data_status": "HEALTHY",
        }
        self.record = {
            "id": self.snapshot_id,
            "raw_json": raw,
            "fetched_at": datetime.now(timezone.utc),
            "stale": False,
            "data_status": "HEALTHY",
        }

    async def get_latest_snapshot(self) -> dict[str, Any] | None:
        self.record["id"] = self.snapshot_id
        return self.record

    async def get_latest_snapshot_meta(self) -> dict[str, Any] | None:
        return {
            "id": self.snapshot_id,
            "fetched_at": self.record["fetched_at"],
            "stale": False,
            "data_status": "HEALTHY",
        }

    async def get_latest_forecasts(self) -> list[dict[str, Any]]:
        return []

    async def get_recommendations(self) -> list[dict[str, Any]]:
        return []

    async def get_depot_risks(self) -> list[dict[str, Any]]:
        return []

    async def get_tick_freshness(self) -> dict[str, float]:
        return {"ticks_per_second": 0.0, "snapshot_age_ticks": 0.0}


@pytest.fixture
def client():
    clear_response_cache()
    try:
        yield TestClient(app)
    finally:
        clear_response_cache()
        app.dependency_overrides.clear()


def test_rate_limiter_scales_with_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1 worker: max requests is 60
    monkeypatch.setenv("API_WORKERS", "1")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "60")
    assert get_rate_limit_max_requests() == 60

    # 4 workers: max requests is 60 // 4 = 15
    monkeypatch.setenv("API_WORKERS", "4")
    assert get_rate_limit_max_requests() == 15

    # 8 workers: max requests is max(10, 60 // 8) = 10
    monkeypatch.setenv("API_WORKERS", "8")
    assert get_rate_limit_max_requests() == 10

    # Test enforcement of scaled limit
    key = "test-worker-scale-key"
    _DECISION_CALLS[key] = []
    limit = get_rate_limit_max_requests()
    for _ in range(limit):
        check_rate_limit(key)

    with pytest.raises(Exception) as exc:
        check_rate_limit(key)
    assert exc.value.status_code == 429


def test_etag_header_and_304_not_modified(client: TestClient) -> None:
    repo = MockSnapshotRepo(snapshot_id=42)
    app.dependency_overrides[get_repository] = lambda: repo

    # Initial GET /api/state returns 200 with ETag header
    res1 = client.get("/api/state")
    assert res1.status_code == 200
    etag = res1.headers.get("etag")
    assert etag is not None
    assert "snap-42" in etag

    # Subsequent GET with If-None-Match matching ETag returns 304 Not Modified
    res2 = client.get("/api/state", headers={"If-None-Match": etag})
    assert res2.status_code == 304
    assert res2.text == ""

    # GET /api/risks also returns 304 when ETag matches
    res_risks1 = client.get("/api/risks")
    assert res_risks1.status_code == 200
    risks_etag = res_risks1.headers.get("etag")
    assert risks_etag is not None
    assert "snap-42" in risks_etag

    res_risks2 = client.get("/api/risks", headers={"If-None-Match": risks_etag})
    assert res_risks2.status_code == 304


def test_cache_invalidation_on_new_snapshot(client: TestClient) -> None:
    repo = MockSnapshotRepo(snapshot_id=100)
    app.dependency_overrides[get_repository] = lambda: repo

    # First request on snapshot 100
    res1 = client.get("/api/state")
    assert res1.status_code == 200
    old_etag = res1.headers.get("etag")
    assert "snap-100" in old_etag

    # Snapshot advances to 101
    repo.snapshot_id = 101

    # Request with old ETag must NOT return 304; must return fresh 200 with new ETag
    res2 = client.get("/api/state", headers={"If-None-Match": old_etag})
    assert res2.status_code == 200
    new_etag = res2.headers.get("etag")
    assert "snap-101" in new_etag
    assert new_etag != old_etag
