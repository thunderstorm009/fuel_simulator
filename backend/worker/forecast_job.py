"""Compute and persist station/fuel risk after each new validated snapshot."""

from __future__ import annotations

import inspect
import json
import logging
from statistics import mean
from typing import Protocol

from core.forecast import expected_demand
from core.metrics import (
    forecast_error_liters,
    forecast_mape,
    forecasts_computed,
    hours_to_stockout_gauge,
    policy_fallbacks,
    stockout_probability,
)
from core.models import FuelType, Snapshot, Station
from core.risk import ForecastRecord, forecast_pair
from worker.forecaster import BaselineForecaster, RemoteForecastError

logger = logging.getLogger("fuel_simulator.worker.forecast")


class Forecaster(Protocol):
    def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord | object: ...


class LocalForecaster:
    """Pure local forecast implementation, replaceable by a remote service later."""

    def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord:
        return forecast_pair(snapshot, station, fuel, seed=seed)


class ForecastStore(Protocol):
    async def persist_forecasts(
        self, snapshot: Snapshot, records: list[ForecastRecord]
    ) -> None: ...

    async def set_predictor_incident(self, active: bool, reason: str | None = None) -> None: ...


class ForecastJob:
    def __init__(
        self,
        store: ForecastStore,
        forecaster: Forecaster | None = None,
        fallback: Forecaster | None = None,
    ) -> None:
        self.store = store
        self.forecaster = forecaster or LocalForecaster()
        self.fallback = fallback or BaselineForecaster()
        self._last_signature: tuple[object, ...] | None = None

    async def run(self, snapshot: Snapshot) -> list[ForecastRecord]:
        signature = (
            snapshot.instance.id,
            snapshot.instance.seed,
            snapshot.instance.tick,
            snapshot.instance.sim_time,
            snapshot.stale,
            snapshot.data_status,
        )
        if signature == self._last_signature:
            return []
        records: list[ForecastRecord] = []
        fallback_reason: str | None = None
        for station in snapshot.stations:
            for fuel_index, fuel in enumerate(FuelType):
                pair_offset = sum(station.id.encode("utf-8")) + fuel_index * 1009
                seed = (
                    snapshot.instance.seed + snapshot.instance.tick * 9176 + pair_offset
                ) % 2**32
                try:
                    record = self.forecaster.forecast(snapshot, station, fuel, seed)
                    if inspect.isawaitable(record):
                        record = await record
                except RemoteForecastError as exc:
                    fallback_reason = fallback_reason or exc.reason
                    policy_fallbacks.labels(reason=exc.reason).inc()
                    logger.warning(
                        json.dumps(
                            {
                                "timestamp": snapshot.fetched_at.isoformat(),
                                "level": "warning",
                                "service": "worker",
                                "event": "predictor_fallback",
                                "tick": snapshot.instance.tick,
                                "correlation_id": None,
                                "reason": exc.reason,
                            }
                        )
                    )
                    record = self.fallback.forecast(snapshot, station, fuel, seed)
                    if inspect.isawaitable(record):
                        record = await record
                assert isinstance(record, ForecastRecord)
                records.append(record)
                forecasts_computed.labels(risk_level=record.forecast.risk_level.value).inc()
                labels = {"station": station.id, "fuel": fuel.value}
                probability = record.forecast.stockout_probability_24h
                stockout_probability.labels(**labels).set(probability)
                hours = record.forecast.hours_to_stockout
                hours_to_stockout_gauge.labels(**labels).set(
                    float(hours) if hours is not None else float("nan")
                )
                self._record_error(snapshot, station, fuel, record)
        await self.store.set_predictor_incident(fallback_reason is not None, fallback_reason)
        await self.store.persist_forecasts(snapshot, records)
        self._last_signature = signature
        return records

    @staticmethod
    def _record_error(
        snapshot: Snapshot,
        station: Station,
        fuel: FuelType,
        record: ForecastRecord,
        *,
        window: int = 12,
    ) -> None:
        history = sorted(
            (
                row
                for row in snapshot.demand_history
                if row.station_id == station.id and row.fuel_type is fuel
            ),
            key=lambda row: (row.tick, row.id),
        )[-window:]
        if not history:
            return
        ratio = float(record.drivers["recent_ratio"])
        errors = []
        percentage_errors = []
        for observation in history:
            baseline = expected_demand(
                station.demand_profile,
                fuel,
                observation.sim_time,
                1.0,
                snapshot.instance.tick_minutes,
            )
            errors.append(abs(observation.demand_liters - baseline * ratio))
            if baseline > 0:
                percentage_errors.append(
                    abs(observation.demand_liters - baseline * ratio) / baseline
                )
        forecast_error_liters.labels(station_id=station.id, fuel_type=fuel.value).set(mean(errors))
        if percentage_errors:
            forecast_mape.labels(station=station.id, fuel=fuel.value).set(mean(percentage_errors))
