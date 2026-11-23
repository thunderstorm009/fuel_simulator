from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.database import PostgresReadRepository
from api.routes.chaos import router as chaos_router
from api.routes.health import router as health_router
from api.routes.policy import router as policy_router
from api.routes.read import router as read_router
from api.routes.recommendations import router as recommendations_router
from api.routes.stream import router as stream_router
from api.stream import EventBroadcaster
from core.metrics import api_http_request_duration, api_http_requests, health_checks


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    app.state.repository = None
    app.state.broadcaster = EventBroadcaster(database_url)
    broadcaster_task = None
    if database_url:
        repository = await PostgresReadRepository.connect(database_url)
        app.state.repository = repository
        broadcaster_task = asyncio.create_task(app.state.broadcaster.run())
    else:
        repository = None
    try:
        yield
    finally:
        if broadcaster_task is not None:
            broadcaster_task.cancel()
        if app.state.broadcaster is not None:
            await app.state.broadcaster.close()
        if repository is not None:
            await repository.close()


app = FastAPI(title="Fuel Supply Platform API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        {
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGIN", "http://localhost:5173,http://localhost:5174"
            ).split(",")
            if origin.strip()
        }
        | {"http://localhost:5173", "http://localhost:5174"}
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(read_router)
app.include_router(health_router)
app.include_router(recommendations_router)
app.include_router(policy_router)
app.include_router(chaos_router)
app.include_router(stream_router)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        route_template = getattr(route, "path", "unmatched")
        method = request.method
        api_http_requests.labels(
            method=method,
            route=route_template,
            status_class=f"{status_code // 100}xx",
        ).inc()
        api_http_request_duration.labels(method=method, route=route_template).observe(
            max(0.0, time.perf_counter() - started)
        )


@app.get("/health")
def health() -> dict[str, str]:
    health_checks.labels(service="api").inc()
    return {"status": "ok", "service": "api"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
