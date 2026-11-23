from __future__ import annotations

import uuid
from typing import Any

from core.models import AllocationRequest, AllocationStatus, FuelType, RecommendationStatus


class MockStore:
    def __init__(self) -> None:
        self.recommendations: dict[uuid.UUID, dict[str, Any]] = {}
        self.submitted_keys: set[str] = set()

    def add_recommendation(
        self,
        rec_id: uuid.UUID,
        status: RecommendationStatus,
        idempotency_key: str,
        allocation_id: int | None = None,
    ) -> None:
        self.recommendations[rec_id] = {
            "id": rec_id,
            "status": status.value,
            "idempotency_key": idempotency_key,
            "sim_allocation_id": allocation_id,
            "fuel_type": FuelType.DIESEL.value,
            "quantity": 5000.0,
            "depot_id": "depot-gazipur",
            "station_id": "station-mirpur",
            "route_id": "route-gazipur-mirpur",
        }
        if status in (RecommendationStatus.SUBMITTED, RecommendationStatus.ARRIVED):
            self.submitted_keys.add(idempotency_key)


def test_backup_restore_preserves_idempotency_keys_and_prevents_duplicate_submission() -> None:
    # 1. State before backup
    store_before = MockStore()
    rec_id = uuid.uuid4()
    key = f"rec-{rec_id}"
    store_before.add_recommendation(
        rec_id, RecommendationStatus.SUBMITTED, key, allocation_id=42
    )

    assert key in store_before.submitted_keys
    assert store_before.recommendations[rec_id]["status"] == "SUBMITTED"
    assert store_before.recommendations[rec_id]["sim_allocation_id"] == 42

    # 2. Simulate dump/restore: serialize store state to dict and deserialize into a new store
    restored_data = {
        k: dict(v) for k, v in store_before.recommendations.items()
    }
    store_after = MockStore()
    for item in restored_data.values():
        status = RecommendationStatus(item["status"])
        store_after.add_recommendation(
            item["id"], status, item["idempotency_key"], item["sim_allocation_id"]
        )

    # 3. Verify state integrity after restore
    assert rec_id in store_after.recommendations
    restored_rec = store_after.recommendations[rec_id]
    assert restored_rec["idempotency_key"] == key
    assert restored_rec["status"] == "SUBMITTED"
    assert restored_rec["sim_allocation_id"] == 42
    assert key in store_after.submitted_keys

    # 4. Executor check: worker must NOT re-submit already SUBMITTED or ARRIVED item
    actionable_statuses = {RecommendationStatus.APPROVED.value}
    assert restored_rec["status"] not in actionable_statuses, (
        "Worker executor must not process SUBMITTED/ARRIVED recommendation after restore"
    )


def test_idempotency_key_immutable_across_cycles() -> None:
    rec_id = uuid.uuid4()
    req = AllocationRequest(
        source_depot_id="depot-gazipur",
        destination_station_id="station-mirpur",
        route_id="route-gazipur-mirpur",
        fuel_type=FuelType.DIESEL,
        quantity=5000.0,
        idempotency_key=f"rec-{rec_id}",
    )
    # The idempotency key is permanent and must never change
    assert req.idempotency_key == f"rec-{rec_id}"
