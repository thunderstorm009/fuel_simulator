"""Remote predictor client and deterministic no-calibration fallback."""

from __future__ import annotations

import asyncio
import time
from typing import Protocol

import httpx

from core.models import FuelType, Snapshot, Station
from core.risk import ForecastRecord, TrajectoryPoint, forecast_pair


class ForecastBackend(Protocol):
    async def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord: ...


class RemoteForecastError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class RemoteForecaster:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_s: float = 1.5,
        failure_threshold: int = 5,
        reset_after_s: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=max(0.1, timeout_s), transport=transport)
        self.failure_threshold = max(1, failure_threshold)
        self.reset_after_s = max(0.1, reset_after_s)
        self._failures = 0
        self._opened_until = 0.0
        self._half_open_probe = False
        self._lock = asyncio.Lock()

    async def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord:
        async with self._lock:
            if self._opened_until:
                if time.monotonic() < self._opened_until or self._half_open_probe:
                    raise RemoteForecastError("breaker_open")
                self._half_open_probe = True
        try:
            station_snapshot = snapshot.model_copy(
                update={
                    "stations": [station],
                    "demand_history": [
                        row
                        for row in snapshot.demand_history
                        if row.station_id == station.id and row.fuel_type is fuel
                    ],
                }
            )
            response = await self.client.post(
                f"{self.base_url}/predict",
                json={
                    "snapshot": station_snapshot.model_dump(mode="json"),
                    "station_id": station.id,
                    "fuel_type": fuel.value,
                    "seed": seed,
                },
            )
            if response.status_code >= 500:
                raise RemoteForecastError("predictor_5xx")
            if response.status_code >= 400:
                raise RemoteForecastError("predictor_rejected_request")
            payload = response.json()
            record = self._parse_record(payload)
            if record.forecast.station_id != station.id or record.forecast.fuel_type is not fuel:
                raise RemoteForecastError("predictor_schema_error")
        except httpx.TimeoutException as exc:
            await self._record_failure()
            raise RemoteForecastError("timeout") from exc
        except httpx.HTTPError as exc:
            await self._record_failure()
            raise RemoteForecastError("unavailable") from exc
        except RemoteForecastError:
            await self._record_failure()
            raise
        except (ValueError, KeyError, TypeError) as exc:
            await self._record_failure()
            raise RemoteForecastError("predictor_schema_error") from exc
        async with self._lock:
            self._failures = 0
            self._opened_until = 0.0
            self._half_open_probe = False
        return record

    async def _record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_until = time.monotonic() + self.reset_after_s
            self._half_open_probe = False

    @staticmethod
    def _parse_record(payload: dict[str, object]) -> ForecastRecord:
        from core.models import Forecast

        forecast = Forecast.model_validate(payload["forecast"])
        trajectory = [TrajectoryPoint(**point) for point in payload["trajectory"]]
        drivers = payload["drivers"]
        source = str(payload.get("source", "remote"))
        return ForecastRecord(forecast, trajectory, drivers, source=source)

    async def close(self) -> None:
        await self.client.aclose()


class BaselineForecaster:
    """Fallback using profile demand only, with review-required confidence capped at 0.4."""

    async def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord:
        baseline_snapshot = snapshot.model_copy(update={"demand_history": []})
        record = forecast_pair(baseline_snapshot, station, fuel, seed=seed)
        forecast = record.forecast.model_copy(
            update={"confidence": min(0.4, record.forecast.confidence), "needs_review": True}
        )
        return ForecastRecord(
            forecast=forecast,
            trajectory=record.trajectory,
            drivers={**record.drivers, "fallback_reason": "predictor_unavailable"},
            source="baseline",
        )
