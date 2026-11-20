from __future__ import annotations

import pytest
from tests.integration.test_ingest import FakeClient, FakeStore
from worker.ingest import SnapshotIngestor

from core.models import DataStatus


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fault", "expected_status"),
    [("unavailable", "DEGRADED"), ("error_rate", "DEGRADED"), ("latency", "DEGRADED")],
)
async def test_transport_faults_keep_last_snapshot_and_mark_degraded(fault, expected_status):
    assert fault in {"unavailable", "error_rate", "latency"}
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(client, store)
    await ingestor.run_once()
    last_good = store.snapshots[0]
    client.failure_method = "get_routes"

    assert await ingestor.run_once() is False
    assert store.snapshots == [last_good]
    assert store.latest_status == expected_status
    assert store.events[-1]["kind"] == "snapshot_rejected"


@pytest.mark.asyncio
async def test_stale_data_fault_is_persisted_as_degraded_and_flagged():
    client = FakeClient()
    client.stale = True
    store = FakeStore()
    await SnapshotIngestor(client, store).run_once()

    assert store.snapshots[0].stale is True
    assert store.snapshots[0].data_status is DataStatus.DEGRADED


@pytest.mark.asyncio
async def test_malformed_data_fault_retains_last_good_snapshot_and_records_rejection():
    client = FakeClient()
    store = FakeStore()
    ingestor = SnapshotIngestor(client, store)
    await ingestor.run_once()
    last_good = store.snapshots[0]
    client.malformed_stations = [{"id": "incomplete"}]

    assert await ingestor.run_once() is False
    assert store.snapshots == [last_good]
    assert store.latest_status == "DEGRADED"
    assert store.events[-1]["kind"] == "snapshot_rejected"
