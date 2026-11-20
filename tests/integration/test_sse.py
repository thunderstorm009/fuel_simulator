from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import pytest
from worker.sse import SSEConsumer, logger

from core.sim_client import SimUnavailable


def test_sse_connection_logs_are_enabled_at_info_level() -> None:
    assert logger.isEnabledFor(logging.INFO)
    assert logger.handlers


class FakeClient:
    def __init__(self, streams: list[Any]) -> None:
        self.streams = streams
        self.connections = 0

    @asynccontextmanager
    async def stream(self):
        stream = self.streams[self.connections]
        self.connections += 1
        if isinstance(stream, Exception):
            raise stream
        yield stream


@pytest.mark.asyncio
async def test_stream_event_refresh_is_rate_limited_and_keepalive_is_ignored() -> None:
    clock = [0.0]
    refreshes = 0

    async def lines():
        yield ": keepalive"
        yield "event: simulation.tick"
        yield 'data: {"tick":1}'
        clock[0] = 1.0
        yield 'data: {"tick":2}'

    async def refresh() -> None:
        nonlocal refreshes
        refreshes += 1

    consumer = SSEConsumer(FakeClient([lines()]), refresh, clock=lambda: clock[0])

    await consumer.run(max_connections=1)

    assert refreshes == 2  # One after connection, one after the rate-limit window.


@pytest.mark.asyncio
async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect(caplog) -> None:
    caplog.set_level(logging.INFO, logger="fuel_simulator.worker.sse")
    refreshes = 0
    delays: list[float] = []

    async def refresh() -> None:
        nonlocal refreshes
        refreshes += 1

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async def one_event():
        yield ": keepalive"

    client = FakeClient([SimUnavailable("stream fault"), one_event()])
    consumer = SSEConsumer(client, refresh, sleep=sleep, clock=lambda: 0.0)

    await consumer.run(max_connections=2)

    assert client.connections == 2
    assert delays == [0.5]
    assert refreshes == 1
    assert '"event": "simulator_stream_connected"' in caplog.text
