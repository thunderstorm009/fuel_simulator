"""SSE hint consumer; REST ingestion remains the only source of snapshot state."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable

from core.metrics import sse_events, sse_reconnects
from core.sim_client import SimClient

logger = logging.getLogger("fuel_simulator.worker.sse")


class SSEConsumer:
    def __init__(
        self,
        client: SimClient,
        refresh: Callable[[], Awaitable[object]],
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        max_backoff_s: float = 30.0,
    ) -> None:
        self.client = client
        self.refresh = refresh
        self._sleep = sleep
        self._clock = clock
        self.max_backoff_s = max_backoff_s
        self._last_refresh = float("-inf")

    async def run(
        self,
        *,
        stop_event: asyncio.Event | None = None,
        max_connections: int | None = None,
    ) -> None:
        backoff_s = 0.5
        connections = 0
        while stop_event is None or not stop_event.is_set():
            connections += 1
            sse_reconnects.inc()
            try:
                async with self.client.stream() as lines:
                    await self._refresh_if_due()
                    backoff_s = 0.5
                    async for line in lines:
                        if stop_event is not None and stop_event.is_set():
                            return
                        if line.startswith("data:"):
                            sse_events.inc()
                            await self._refresh_if_due()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    json.dumps(
                        {
                            "event": "simulator_stream_disconnected",
                            "error_type": type(exc).__name__,
                        }
                    )
                )

            if max_connections is not None and connections >= max_connections:
                return
            if stop_event is not None and stop_event.is_set():
                return
            await self._sleep(backoff_s)
            backoff_s = min(backoff_s * 2, self.max_backoff_s)

    async def _refresh_if_due(self) -> None:
        now = self._clock()
        if now - self._last_refresh < 1.0:
            return
        self._last_refresh = now
        await self.refresh()
