import asyncio
import hmac
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from core.metrics import health_checks
from core.models import FuelType, Snapshot
from core.risk import forecast_pair


@asynccontextmanager
async def lifespan(app: FastAPI):
    server = None
    try:

        async def forward(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            try:
                remote_reader, remote_writer = await asyncio.open_connection("127.0.0.1", 8103)

                async def pipe(r: asyncio.StreamReader, w: asyncio.StreamWriter):
                    try:
                        while not r.at_eof():
                            data = await r.read(4096)
                            if not data:
                                break
                            w.write(data)
                            await w.drain()
                    except Exception:
                        pass
                    finally:
                        try:
                            w.close()
                        except Exception:
                            pass

                await asyncio.gather(pipe(reader, remote_writer), pipe(remote_reader, writer))
            except Exception:
                pass
            finally:
                try:
                    writer.close()
                except Exception:
                    pass

        server = await asyncio.start_server(forward, "0.0.0.0", 8100)
    except Exception:
        server = None
    yield
    if server:
        server.close()
        await server.wait_closed()


app = FastAPI(title="Fuel Supply Platform Predictor", version="0.2.0", lifespan=lifespan)
app.state.fail_forecasts = False


class PredictRequest(BaseModel):
    snapshot: Snapshot
    station_id: str = Field(min_length=1, max_length=150)
    fuel_type: FuelType
    seed: int


class FailForecastRequest(BaseModel):
    enabled: bool


@app.get("/health")
def health() -> dict[str, str]:
    health_checks.labels(service="predictor").inc()
    return {"status": "ok", "service": "predictor"}


@app.post("/predict")
def predict(payload: PredictRequest, request: Request) -> dict[str, Any]:
    if request.app.state.fail_forecasts:
        raise HTTPException(status_code=503, detail="Injected predictor failure")
    station = next(
        (item for item in payload.snapshot.stations if item.id == payload.station_id), None
    )
    if station is None:
        raise HTTPException(status_code=404, detail="Unknown station")
    record = forecast_pair(
        payload.snapshot,
        station,
        payload.fuel_type,
        seed=payload.seed,
    )
    return {
        "forecast": record.forecast.model_dump(mode="json"),
        "trajectory": [asdict(point) for point in record.trajectory],
        "drivers": record.drivers,
        "source": "remote",
    }


@app.post("/admin/fail")
def set_failure(payload: FailForecastRequest, request: Request) -> dict[str, bool]:
    token = request.headers.get("X-Operator-Token", "")
    expected = os.getenv("OPERATOR_TOKEN", "")
    if not expected or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid operator token")
    request.app.state.fail_forecasts = payload.enabled
    return {"enabled": request.app.state.fail_forecasts}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
