"""Compute and persist station/fuel risk after each new validated snapshot."""

from __future__ import annotations

from statistics import mean
from typing import Protocol

from core.forecast import expected_demand
from core.metrics import forecast_error_liters, forecasts_computed
from core.models import FuelType, Snapshot, Station
from core.risk import ForecastRecord, forecast_pair


class Forecaster(Protocol):
    def forecast(
        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    ) -> ForecastRecord: ...


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


class ForecastJob:
    def __init__(self, store: ForecastStore, forecaster: Forecaster | None = None) -> None:
        self.store = store
        self.forecaster = forecaster or LocalForecaster()
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
        for station in snapshot.stations:
            for fuel_index, fuel in enumerate(FuelType):
                pair_offset = sum(station.id.encode("utf-8")) + fuel_index * 1009
                seed = (
                    snapshot.instance.seed + snapshot.instance.tick * 9176 + pair_offset
                ) % 2**32
                record = self.forecaster.forecast(snapshot, station, fuel, seed)
                records.append(record)
                forecasts_computed.labels(risk_level=record.forecast.risk_level.value).inc()
                self._record_error(snapshot, station, fuel, record)
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
        for observation in history:
            baseline = expected_demand(
                station.demand_profile,
                fuel,
                observation.sim_time,
                1.0,
                snapshot.instance.tick_minutes,
            )
            errors.append(abs(observation.demand_liters - baseline * ratio))
        forecast_error_liters.labels(station_id=station.id, fuel_type=fuel.value).set(mean(errors))
