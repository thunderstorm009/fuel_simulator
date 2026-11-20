"""Typed, bounded-retry client for the official fuel simulator."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter, ValidationError
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt

from core.metrics import (
    sim_breaker_state,
    sim_client_failures,
    sim_client_requests,
    sim_client_retries,
)
from core.models import (
    Allocation,
    DemandObs,
    Depot,
    Instance,
    Metrics,
    Region,
    Route,
    SimEvent,
    Station,
    SupplyArrival,
    parse_sim_error,
)

T = TypeVar("T")
ModelType = Any


@dataclass(frozen=True)
class SimResult(Generic[T]):
    data: T
    stale: bool = False


class SimUnavailable(RuntimeError):
    """The simulator cannot currently serve a valid request."""


class SimInvalidResponse(RuntimeError):
    """The simulator returned malformed JSON or a schema-invalid response."""


class SimBusinessError(RuntimeError):
    """A non-retryable simulator validation or business error."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Per-client breaker; only one request may probe a half-open breaker."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        reset_after_s: float = 10.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_after_s = reset_after_s
        self._clock = clock
        self._state = BreakerState.CLOSED
        self._failure_count = 0
        self._opened_at = 0.0
        self._probe_in_flight = False
        self._lock = asyncio.Lock()
        self._update_metric()

    @property
    def state(self) -> BreakerState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def before_request(self) -> None:
        async with self._lock:
            if self._state is BreakerState.OPEN:
                if self._clock() - self._opened_at < self.reset_after_s:
                    raise SimUnavailable("circuit breaker is open")
                self._state = BreakerState.HALF_OPEN
                self._probe_in_flight = False
                self._update_metric()
            if self._state is BreakerState.HALF_OPEN:
                if self._probe_in_flight:
                    raise SimUnavailable("circuit breaker half-open probe is in flight")
                self._probe_in_flight = True

    async def record_success(self) -> None:
        async with self._lock:
            self._state = BreakerState.CLOSED
            self._failure_count = 0
            self._probe_in_flight = False
            self._update_metric()

    async def record_failure(self) -> None:
        async with self._lock:
            self._probe_in_flight = False
            if self._state is BreakerState.HALF_OPEN:
                self._state = BreakerState.OPEN
                self._opened_at = self._clock()
            else:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = BreakerState.OPEN
                    self._opened_at = self._clock()
            self._update_metric()

    def _update_metric(self) -> None:
        for state in BreakerState:
            sim_breaker_state.labels(state=state.value).set(float(state is self._state))


class _RetryableRequest(RuntimeError):
    pass


class SimClient:
    """Async client that returns validated models and preserves stale markers."""

    def __init__(
        self,
        base_url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        jitter: Callable[[float], float] | None = None,
        max_retries: int = 3,
        connect_timeout_s: float = 2.0,
        read_timeout_s: float = 3.0,
        stream_read_timeout_s: float = 20.0,
        breaker_failure_threshold: int = 5,
        breaker_reset_after_s: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._sleep = sleep
        self._jitter = jitter or (lambda upper: random.uniform(0.0, upper))
        self.max_retries = max_retries
        self.connect_timeout_s = max(0.1, connect_timeout_s)
        self.read_timeout_s = max(0.1, read_timeout_s)
        # The simulator sends an SSE keepalive every 15s; give it room to arrive.
        self.stream_read_timeout_s = max(16.0, stream_read_timeout_s)
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=self.connect_timeout_s,
                read=self.read_timeout_s,
                write=self.read_timeout_s,
                pool=self.connect_timeout_s,
            ),
        )
        self.breaker = CircuitBreaker(
            clock=clock,
            failure_threshold=breaker_failure_threshold,
            reset_after_s=breaker_reset_after_s,
        )

    async def __aenter__(self) -> SimClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def get_health(self) -> SimResult[dict[str, Any]]:
        return await self._get("/v1/health", "/v1/health", dict[str, Any])

    async def get_instance(self) -> SimResult[Instance]:
        return await self._get("/v1/instance", "/v1/instance", Instance)

    async def get_regions(self) -> SimResult[list[Region]]:
        return await self._get("/v1/regions", "/v1/regions", TypeAdapter(list[Region]))

    async def get_depots(self) -> SimResult[list[Depot]]:
        return await self._get("/v1/depots", "/v1/depots", TypeAdapter(list[Depot]))

    async def get_depot(self, entity_id: str) -> SimResult[Depot]:
        path = f"/v1/depots/{quote(entity_id, safe='')}"
        return await self._get(path, "/v1/depots/{entity_id}", Depot)

    async def get_stations(self) -> SimResult[list[Station]]:
        return await self._get("/v1/stations", "/v1/stations", TypeAdapter(list[Station]))

    async def get_station(self, entity_id: str) -> SimResult[Station]:
        path = f"/v1/stations/{quote(entity_id, safe='')}"
        return await self._get(path, "/v1/stations/{entity_id}", Station)

    async def get_routes(self) -> SimResult[list[Route]]:
        return await self._get("/v1/routes", "/v1/routes", TypeAdapter(list[Route]))

    async def get_supply_arrivals(self) -> SimResult[list[SupplyArrival]]:
        return await self._get(
            "/v1/supply-arrivals", "/v1/supply-arrivals", TypeAdapter(list[SupplyArrival])
        )

    async def get_events(self) -> SimResult[list[SimEvent]]:
        return await self._get("/v1/events", "/v1/events", TypeAdapter(list[SimEvent]))

    async def get_allocations(self) -> SimResult[list[Allocation]]:
        return await self._get("/v1/allocations", "/v1/allocations", TypeAdapter(list[Allocation]))

    async def get_metrics(self) -> SimResult[Metrics]:
        return await self._get("/v1/metrics", "/v1/metrics", Metrics)

    async def get_demand_history(
        self, station_id: str | None = None, *, limit: int = 100
    ) -> SimResult[list[DemandObs]]:
        if not 1 <= limit <= 2000:
            raise ValueError("demand-history limit must be between 1 and 2000")
        params: dict[str, Any] = {"limit": limit}
        if station_id is not None:
            params["station_id"] = station_id
        return await self._get(
            "/v1/demand-history",
            "/v1/demand-history",
            TypeAdapter(list[DemandObs]),
            params=params,
        )

    async def create_allocation(self, body: Mapping[str, Any]) -> SimResult[Allocation]:
        stable_body = dict(body)
        return await self._request(
            "POST",
            "/v1/allocations",
            "/v1/allocations",
            Allocation,
            json_body=stable_body,
        )

    @asynccontextmanager
    async def stream(self) -> AsyncIterator[AsyncIterator[str]]:
        endpoint = "/v1/stream"
        await self.breaker.before_request()
        try:
            stream_timeout = httpx.Timeout(
                connect=self.connect_timeout_s,
                read=self.stream_read_timeout_s,
                write=self.read_timeout_s,
                pool=self.connect_timeout_s,
            )
            async with self._http.stream("GET", endpoint, timeout=stream_timeout) as response:
                if response.is_error:
                    content = await response.aread()
                    error_response = httpx.Response(
                        response.status_code, headers=response.headers, content=content
                    )
                    parsed = parse_sim_error(error_response)
                    if response.status_code == 503 and parsed.code == "FAULT_INJECTED":
                        raise SimUnavailable(parsed.message)
                    raise SimBusinessError(parsed.code, parsed.message, response.status_code)
                sim_client_requests.labels(endpoint=endpoint, outcome="success").inc()
                await self.breaker.record_success()
                yield response.aiter_lines()
        except SimBusinessError:
            await self.breaker.record_success()
            sim_client_requests.labels(endpoint=endpoint, outcome="business_error").inc()
            raise
        except (SimUnavailable, httpx.TransportError) as exc:
            await self.breaker.record_failure()
            sim_client_failures.labels(endpoint=endpoint).inc()
            sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
            if isinstance(exc, SimUnavailable):
                raise
            raise SimUnavailable(str(exc)) from exc

    async def _get(
        self,
        path: str,
        endpoint: str,
        response_type: ModelType,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> SimResult[Any]:
        return await self._request("GET", path, endpoint, response_type, params=params)

    async def _request(
        self,
        method: str,
        path: str,
        endpoint: str,
        response_type: ModelType,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> SimResult[Any]:
        await self.breaker.before_request()

        def wait_for_retry(retry_state: Any) -> float:
            base = min(0.2 * (2 ** (retry_state.attempt_number - 1)), 0.8)
            return base + max(0.0, self._jitter(base))

        def count_retry(_: Any) -> None:
            sim_client_retries.labels(endpoint=endpoint).inc()

        retryer = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries + 1),
            retry=retry_if_exception_type(
                (_RetryableRequest, httpx.TimeoutException, httpx.ConnectError)
            ),
            wait=wait_for_retry,
            sleep=self._sleep,
            before_sleep=count_retry,
            reraise=True,
        )
        try:
            async for attempt in retryer:
                with attempt:
                    response = await self._http.request(
                        method,
                        path,
                        params=params,
                        json=json_body,
                    )
                    if response.status_code == 503:
                        parsed = parse_sim_error(response)
                        if parsed.code == "FAULT_INJECTED":
                            raise _RetryableRequest(parsed.message)
                    break
        except (_RetryableRequest, httpx.TimeoutException, httpx.ConnectError) as exc:
            await self.breaker.record_failure()
            sim_client_failures.labels(endpoint=endpoint).inc()
            sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
            raise SimUnavailable(str(exc) or "simulator unavailable") from exc

        if response.is_error:
            parsed = parse_sim_error(response)
            if response.status_code >= 500:
                await self.breaker.record_failure()
                sim_client_failures.labels(endpoint=endpoint).inc()
                sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
                raise SimUnavailable(parsed.message)
            await self.breaker.record_success()
            sim_client_requests.labels(endpoint=endpoint, outcome="business_error").inc()
            raise SimBusinessError(parsed.code, parsed.message, response.status_code)

        try:
            payload = response.json()
            adapter = (
                response_type
                if isinstance(response_type, TypeAdapter)
                else TypeAdapter(response_type)
            )
            data = adapter.validate_python(payload)
        except (ValueError, ValidationError, TypeError) as exc:
            await self.breaker.record_failure()
            sim_client_failures.labels(endpoint=endpoint).inc()
            sim_client_requests.labels(endpoint=endpoint, outcome="invalid_response").inc()
            raise SimInvalidResponse(f"invalid simulator response from {endpoint}: {exc}") from exc

        await self.breaker.record_success()
        sim_client_requests.labels(endpoint=endpoint, outcome="success").inc()
        stale = response.headers.get("X-Simulator-Stale", "").lower() == "true"
        return SimResult(data=data, stale=stale)
