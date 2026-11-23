from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import asyncpg

from core.metrics import sse_clients_connected

logger = logging.getLogger("api.stream")


class EventBroadcaster:
    def __init__(
        self,
        database_url: str | None,
        max_clients: int | None = None,
        reconnect_backoff: float = 1.0,
    ) -> None:
        self.database_url = database_url
        if max_clients is None:
            self.max_clients = int(os.getenv("SSE_MAX_CLIENTS", "50"))
        else:
            self.max_clients = max_clients
        self.reconnect_backoff = reconnect_backoff
        self.subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._stop_event = asyncio.Event()
        self._conn: asyncpg.Connection | None = None

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        if len(self.subscribers) >= self.max_clients:
            raise ConnectionError(
                f"SSE client limit reached ({len(self.subscribers)}/{self.max_clients})"
            )
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self.subscribers.add(queue)
        sse_clients_connected.inc()
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            sse_clients_connected.dec()

    def broadcast(self, event: dict[str, Any]) -> None:
        for queue in list(self.subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def _on_notify(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                self.broadcast(data)
            else:
                self.broadcast({"type": "message", "payload": data})
        except Exception:
            logger.warning("failed to decode event payload: %s", payload)

    async def run(self) -> None:
        if not self.database_url:
            return
        backoff = self.reconnect_backoff
        while not self._stop_event.is_set():
            try:
                self._conn = await asyncpg.connect(self.database_url)
                await self._conn.add_listener("platform_events", self._on_notify)
                logger.info("SSE broadcaster listening to PostgreSQL platform_events")
                backoff = self.reconnect_backoff
                while not self._stop_event.is_set() and not self._conn.is_closed():
                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(
                    "SSE listener connection error: %s. Reconnecting in %.1fs...",
                    exc,
                    backoff,
                )
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 10.0)
            finally:
                if self._conn and not self._conn.is_closed():
                    try:
                        await self._conn.remove_listener("platform_events", self._on_notify)
                        await self._conn.close()
                    except Exception:
                        pass
                    self._conn = None

    async def close(self) -> None:
        self._stop_event.set()
        if self._conn and not self._conn.is_closed():
            try:
                await self._conn.close()
            except Exception:
                pass
            self._conn = None
        for queue in list(self.subscribers):
            self.unsubscribe(queue)
