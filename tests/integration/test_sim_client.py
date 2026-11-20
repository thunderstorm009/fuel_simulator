import json

import httpx
import pytest
import respx

from core.models import Allocation, Instance
from core.sim_client import (
    BreakerState,
    SimBusinessError,
    SimClient,
    SimInvalidResponse,
    SimUnavailable,
)

INSTANCE = {
    "id": 1,
    "scenario_id": "baseline",
    "scenario_version": "1.0",
    "seed": 12345,
    "sim_time": "2026-01-01T00:00:00",
    "tick": 0,
    "tick_minutes": 15,
    "status": "PAUSED",
}


@pytest.mark.asyncio
@respx.mock
async def test_get_instance_returns_typed_result_and_stale_flag() -> None:
    respx.get("http://sim.test/v1/instance").mock(
        return_value=httpx.Response(200, json=INSTANCE, headers={"X-Simulator-Stale": "true"})
    )
    async with SimClient("http://sim.test") as client:
        result = await client.get_instance()
    assert isinstance(result.data, Instance)
    assert result.data.tick_minutes == 15
    assert result.stale is True


@pytest.mark.asyncio
@respx.mock
async def test_malformed_json_and_missing_fields_raise_invalid_response() -> None:
    route = respx.get("http://sim.test/v1/instance").mock(
        side_effect=[httpx.Response(200, text="not-json"), httpx.Response(200, json={"id": 1})]
    )
    async with SimClient("http://sim.test", max_retries=0) as client:
        with pytest.raises(SimInvalidResponse):
            await client.get_instance()
        with pytest.raises(SimInvalidResponse):
            await client.get_instance()
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_business_errors_are_typed_and_not_retried() -> None:
    route = respx.get("http://sim.test/v1/instance").mock(
        return_value=httpx.Response(
            409, json={"detail": {"code": "ROUTE_DISRUPTED", "message": "route closed"}}
        )
    )
    async with SimClient("http://sim.test") as client:
        with pytest.raises(SimBusinessError) as caught:
            await client.get_instance()
    assert caught.value.code == "ROUTE_DISRUPTED"
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_validation_error_and_timeout_behavior() -> None:
    validation_route = respx.get("http://sim.test/v1/instance").mock(
        return_value=httpx.Response(
            422,
            json={"detail": [{"loc": ["body", "tick"], "msg": "invalid"}]},
        )
    )
    async with SimClient("http://sim.test") as client:
        with pytest.raises(SimBusinessError) as caught:
            await client.get_instance()
    assert caught.value.code == "VALIDATION_ERROR"
    assert validation_route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_connection_timeout_retries_then_succeeds_without_real_sleep() -> None:
    route = respx.get("http://sim.test/v1/instance").mock(
        side_effect=[
            httpx.ConnectTimeout("connect timeout"),
            httpx.Response(200, json=INSTANCE),
        ]
    )
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async with SimClient("http://sim.test", sleep=sleep, jitter=lambda _: 0) as client:
        result = await client.get_instance()
    assert result.data.tick == 0
    assert route.call_count == 2
    assert delays == [0.2]


@pytest.mark.asyncio
@respx.mock
async def test_fault_injected_retries_with_bounded_jittered_backoff() -> None:
    route = respx.get("http://sim.test/v1/instance").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}),
            httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}}),
            httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}}),
            httpx.Response(200, json=INSTANCE),
        ]
    )
    delays: list[float] = []

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async with SimClient("http://sim.test", sleep=sleep, jitter=lambda _: 0.05) as client:
        result = await client.get_instance()
    assert result.data.tick == 0
    assert route.call_count == 4
    assert delays == pytest.approx([0.25, 0.45, 0.85])


@pytest.mark.asyncio
@respx.mock
async def test_post_retry_reuses_identical_idempotent_body() -> None:
    request_body = {
        "idempotency_key": "rec-fixed",
        "source_depot_id": "depot-gazipur",
        "destination_station_id": "station-mirpur",
        "route_id": "route-gazipur-mirpur",
        "fuel_type": "DIESEL",
        "quantity": 100,
    }
    response = {
        "id": 1,
        **request_body,
        "created_tick": 0,
        "departure_tick": None,
        "expected_arrival_tick": None,
        "actual_arrival_tick": None,
        "status": "PENDING",
        "failure_reason": None,
    }
    route = respx.post("http://sim.test/v1/allocations").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}),
            httpx.Response(201, json=response),
        ]
    )
    async with SimClient(
        "http://sim.test", sleep=lambda _: _no_sleep(), jitter=lambda _: 0
    ) as client:
        result = await client.create_allocation(request_body)
    assert isinstance(result.data, Allocation)
    assert route.call_count == 2
    assert [json.loads(call.request.content) for call in route.calls] == [request_body] * 2


async def _no_sleep() -> None:
    return None


@pytest.mark.asyncio
@respx.mock
async def test_breaker_opens_then_half_open_probe_closes_it() -> None:
    now = [0.0]
    route = respx.get("http://sim.test/v1/instance").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}) for _ in range(5)
        ]
        + [httpx.Response(200, json=INSTANCE)]
    )
    async with SimClient("http://sim.test", max_retries=0, clock=lambda: now[0]) as client:
        for _ in range(5):
            with pytest.raises(SimUnavailable):
                await client.get_instance()
        assert client.breaker.state is BreakerState.OPEN
        with pytest.raises(SimUnavailable, match="circuit breaker"):
            await client.get_instance()
        assert route.call_count == 5
        now[0] = 10.1
        result = await client.get_instance()
    assert result.data.tick == 0
    assert client.breaker.state is BreakerState.CLOSED


@pytest.mark.asyncio
@respx.mock
async def test_demand_history_always_sends_bounded_limit_and_station() -> None:
    rows = [
        {
            "id": 1,
            "station_id": "station-mirpur",
            "fuel_type": "DIESEL",
            "tick": 0,
            "sim_time": "2026-01-01T00:00:00",
            "demand_liters": 100,
            "served_liters": 90,
            "unmet_liters": 10,
        }
    ]
    route = respx.get("http://sim.test/v1/demand-history").mock(
        return_value=httpx.Response(200, json=rows)
    )
    async with SimClient("http://sim.test") as client:
        await client.get_demand_history("station-mirpur", limit=100)
    assert route.calls[0].request.url.params["limit"] == "100"
    assert route.calls[0].request.url.params["station_id"] == "station-mirpur"


@pytest.mark.asyncio
@respx.mock
async def test_stream_fault_is_typed_for_reconnect_owner() -> None:
    respx.get("http://sim.test/v1/stream").mock(
        return_value=httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}})
    )
    async with SimClient("http://sim.test") as client:
        with pytest.raises(SimUnavailable):
            async with client.stream():
                pass


@pytest.mark.asyncio
async def test_stream_read_timeout_exceeds_documented_keepalive_interval() -> None:
    timeouts = []

    async def handler(request: httpx.Request) -> httpx.Response:
        timeouts.append(request.extensions["timeout"])
        return httpx.Response(200, text=": connected\n")

    async with httpx.AsyncClient(
        base_url="http://sim.test",
        transport=httpx.MockTransport(handler),
        timeout=httpx.Timeout(3.0),
    ) as http_client:
        async with SimClient(
            "http://sim.test",
            http_client=http_client,
            read_timeout_s=3.0,
            stream_read_timeout_s=20.0,
        ) as client:
            async with client.stream() as lines:
                assert [line async for line in lines] == [": connected"]

    assert timeouts[0]["read"] >= 20.0


@pytest.mark.asyncio
@respx.mock
async def test_stream_reconnects_do_not_restart_open_breaker_cooldown() -> None:
    now = [0.0]
    respx.get("http://sim.test/v1/instance").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}),
            httpx.Response(200, json=INSTANCE),
        ]
    )
    respx.get("http://sim.test/v1/stream").mock(return_value=httpx.Response(200, text=""))
    async with SimClient(
        "http://sim.test",
        max_retries=0,
        breaker_failure_threshold=1,
        clock=lambda: now[0],
    ) as client:
        with pytest.raises(SimUnavailable):
            await client.get_instance()
        now[0] = 6.0
        with pytest.raises(SimUnavailable, match="circuit breaker"):
            async with client.stream():
                pass
        now[0] = 10.1
        result = await client.get_instance()

    assert result.data.tick == 0
