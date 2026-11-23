from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.stream import stream_events
from api.stream import EventBroadcaster
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_event_broadcaster_delivers_event_to_subscriber() -> None:
    broadcaster = EventBroadcaster("mock_db_url", max_clients=5)
    queue = broadcaster.subscribe()

    assert queue in broadcaster.subscribers
    assert queue.empty()

    # Broadcast an event
    broadcaster.broadcast({"type": "snapshot", "tick": 42})

    assert not queue.empty()
    item = queue.get_nowait()
    assert item["type"] == "snapshot"
    assert item["tick"] == 42

    broadcaster.unsubscribe(queue)
    assert queue not in broadcaster.subscribers


@pytest.mark.asyncio
async def test_broadcaster_bounded_queue_drops_oldest_on_overflow() -> None:
    broadcaster = EventBroadcaster("mock_db_url", max_clients=5)
    queue = broadcaster.subscribe()

    # Fill queue to its maxsize
    for i in range(100):
        broadcaster.broadcast({"type": "snapshot", "tick": i})

    # Queue should be full (100 items)
    assert queue.full()

    # Broadcasting one more should drop oldest (tick 0) and append tick 100 without raising
    broadcaster.broadcast({"type": "snapshot", "tick": 100})
    assert queue.full()

    first_item = queue.get_nowait()
    # The oldest item remaining should be tick 1 (tick 0 was dropped)
    assert first_item["tick"] == 1

    broadcaster.unsubscribe(queue)


@pytest.mark.asyncio
async def test_broadcaster_enforces_max_clients_limit() -> None:
    broadcaster = EventBroadcaster("mock_db_url", max_clients=2)
    q1 = broadcaster.subscribe()
    q2 = broadcaster.subscribe()

    with pytest.raises(ConnectionError) as exc:
        broadcaster.subscribe()
    assert "limit reached" in str(exc.value)

    broadcaster.unsubscribe(q1)
    broadcaster.unsubscribe(q2)


@pytest.mark.asyncio
async def test_stream_endpoint_returns_events_and_heartbeat() -> None:
    broadcaster = EventBroadcaster(None, max_clients=10)
    req = MagicMock()
    req.app.state.broadcaster = broadcaster
    req.is_disconnected = AsyncMock(return_value=False)

    resp = await stream_events(req)
    assert resp.status_code == 200
    assert resp.media_type == "text/event-stream"
    assert resp.headers["Cache-Control"] == "no-cache"

    gen = resp.body_iterator
    # 1. Connected event
    first_chunk = await gen.__anext__()
    assert "event: connected\ndata: {}\n\n" in first_chunk

    # 2. Broadcast event
    broadcaster.broadcast({"type": "snapshot", "tick": 99})
    second_chunk = await gen.__anext__()
    assert 'event: snapshot\ndata: {"type":"snapshot","tick":99}\n\n' in second_chunk

    # 3. Clean unsubscribe on generator close
    await gen.aclose()
    assert len(broadcaster.subscribers) == 0


@pytest.mark.asyncio
async def test_stream_endpoint_returns_429_when_limit_reached() -> None:
    broadcaster = EventBroadcaster(None, max_clients=1)
    req = MagicMock()
    req.app.state.broadcaster = broadcaster
    req.is_disconnected = AsyncMock(return_value=False)

    # Fill the limit
    q = broadcaster.subscribe()

    with pytest.raises(HTTPException) as exc:
        await stream_events(req)
    assert exc.value.status_code == 429
    assert "limit reached" in str(exc.value.detail)

    broadcaster.unsubscribe(q)


@pytest.mark.asyncio
async def test_stream_endpoint_heartbeat_ping() -> None:
    broadcaster = EventBroadcaster(None, max_clients=10)
    req = MagicMock()
    req.app.state.broadcaster = broadcaster
    req.is_disconnected = AsyncMock(return_value=False)

    resp = await stream_events(req)
    gen = resp.body_iterator

    # First is connected
    first = await gen.__anext__()
    assert "event: connected" in first

    # Mock wait_for to raise TimeoutError to trigger heartbeat
    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        ping = await gen.__anext__()
        assert ping == ": ping\n\n"

    await gen.aclose()


@pytest.mark.asyncio
async def test_broadcaster_survives_transient_db_disconnection() -> None:
    broadcaster = EventBroadcaster("mock_db_url", reconnect_backoff=0.01)
    attempts = 0

    async def mock_connect(url: str):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionRefusedError("db temporarily unreachable")
        conn = AsyncMock()
        conn.is_closed = MagicMock(return_value=False)
        conn.close.side_effect = lambda: conn.is_closed.configure_mock(return_value=True)
        return conn

    with patch("api.stream.asyncpg.connect", side_effect=mock_connect):
        task = asyncio.create_task(broadcaster.run())
        for _ in range(10):
            if attempts >= 2:
                break
            await asyncio.sleep(0.02)
        await broadcaster.close()
        await task

    assert attempts >= 2
