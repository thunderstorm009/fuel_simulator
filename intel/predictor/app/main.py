from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core.metrics import health_checks

app = FastAPI(title="Fuel Supply Platform Predictor", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    health_checks.labels(service="predictor").inc()
    return {"status": "ok", "service": "predictor"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
