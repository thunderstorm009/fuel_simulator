from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core.metrics import health_checks, recommendation_job_failures
from core.sim_client import SimClient
from worker.executor import Executor
from worker.forecast_job import ForecastJob
from worker.forecaster import RemoteForecaster
from worker.ingest import SnapshotIngestor
from worker.recommend_job import RecommendationJob
from worker.sse import SSEConsumer
from worker.store import PostgresStore

logger = logging.getLogger("fuel_simulator.worker.main")


async def _wait_for_stop(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=seconds)
    except TimeoutError:
        pass


async def _poll_loop(ingestor: SnapshotIngestor, interval_s: float, stop: asyncio.Event) -> None:
    while not stop.is_set():
        started = asyncio.get_running_loop().time()
        await ingestor.run_once()
        elapsed = asyncio.get_running_loop().time() - started
        await _wait_for_stop(stop, max(0.0, interval_s - elapsed))


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        yield
        return

    store = await PostgresStore.connect(database_url)
    client = SimClient(
        os.getenv("SIM_BASE_URL", "http://localhost:8000"),
        max_retries=max(0, int(os.getenv("SIM_MAX_RETRIES", "3"))),
        connect_timeout_s=max(0.1, float(os.getenv("SIM_CONNECT_TIMEOUT_S", "2"))),
        read_timeout_s=max(0.1, float(os.getenv("SIM_READ_TIMEOUT_S", "3"))),
        stream_read_timeout_s=max(16.0, float(os.getenv("SIM_STREAM_READ_TIMEOUT_S", "20"))),
        breaker_failure_threshold=max(1, int(os.getenv("SIM_BREAKER_FAILURE_THRESHOLD", "5"))),
        breaker_reset_after_s=max(0.1, float(os.getenv("SIM_BREAKER_RESET_S", "10"))),
    )
    predictor = RemoteForecaster(
        os.getenv("PREDICTOR_URL", "http://predictor:8103"),
        timeout_s=max(0.1, float(os.getenv("PREDICTOR_TIMEOUT_S", "1.5"))),
        failure_threshold=max(1, int(os.getenv("PREDICTOR_BREAKER_FAILURE_THRESHOLD", "5"))),
        reset_after_s=max(0.1, float(os.getenv("PREDICTOR_BREAKER_RESET_S", "10"))),
    )
    forecast_job = ForecastJob(store, predictor)
    recommendation_job = RecommendationJob(store)

    async def process_snapshot(snapshot):
        forecasts = await forecast_job.run(snapshot)
        if forecasts:
            try:
                await recommendation_job.run(snapshot, forecasts)
                await store.heartbeat(
                    "decision_engine",
                    {"tick": snapshot.instance.tick, "status": "ok"},
                )
            except Exception as exc:
                recommendation_job_failures.inc()
                logger.exception(
                    json.dumps(
                        {
                            "event": "recommendation_job_failed",
                            "tick": snapshot.instance.tick,
                            "error_type": type(exc).__name__,
                        }
                    )
                )

    ingestor = SnapshotIngestor(client, store, on_snapshot=process_snapshot)
    executor = Executor(store, client, ingestor.fetch_snapshot)
    stop = asyncio.Event()
    app.state.store = store
    app.state.sim_client = client
    app.state.ingestor = ingestor
    app.state.executor = executor
    await ingestor.run_once()
    interval_s = max(0.1, float(os.getenv("INGEST_INTERVAL_S", "5")))
    poll_task = asyncio.create_task(_poll_loop(ingestor, interval_s, stop))
    sse_task = asyncio.create_task(SSEConsumer(client, ingestor.run_once).run(stop_event=stop))
    executor_task = asyncio.create_task(executor.run(stop))
    try:
        yield
    finally:
        stop.set()
        for task in (poll_task, sse_task, executor_task):
            task.cancel()
        await asyncio.gather(poll_task, sse_task, return_exceptions=True)
        await predictor.close()
        await client.close()
        await store.close()


app = FastAPI(title="Fuel Supply Platform Worker", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    health_checks.labels(service="worker").inc()
    return {"status": "ok", "service": "worker"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
