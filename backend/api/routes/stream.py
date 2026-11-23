from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.stream import EventBroadcaster
from core.metrics import sse_events_sent_total

router = APIRouter(tags=["stream"])
logger = logging.getLogger("api.routes.stream")


@router.get("/api/stream")
async def stream_events(request: Request) -> StreamingResponse:
    broadcaster: EventBroadcaster | None = getattr(request.app.state, "broadcaster", None)
    if broadcaster is None:
        raise HTTPException(status_code=503, detail="event stream not configured")

    try:
        queue = broadcaster.subscribe()
    except ConnectionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    event_type = str(item.get("type", "message"))
                    sse_events_sent_total.labels(event_type=event_type).inc()
                    data_str = json.dumps(item, separators=(",", ":"))
                    yield f"event: {event_type}\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                if await request.is_disconnected():
                    break
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
