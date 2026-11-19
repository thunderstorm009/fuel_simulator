#!/usr/bin/env python3
"""Capture the official simulator's REST, event, fault, and idempotency behavior."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "docs" / "sim-samples"
EVENT_TYPES = (
    "demand_spike",
    "route_disruption",
    "station_outage",
    "depot_constraint",
    "shipment_delay",
    "supply_shortfall",
)
FAULT_TYPES = ("latency", "unavailable", "error_rate", "stale_data", "stream_disconnect")


def body_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {"type": "object", "keys": sorted(value)}
    if isinstance(value, list):
        return {
            "type": "array",
            "length": len(value),
            "first_item_keys": sorted(value[0]) if value and isinstance(value[0], dict) else [],
        }
    return {"type": type(value).__name__}


def sample_path(name: str, directory: Path = SAMPLES) -> Path:
    """Return a sample path without duplicating an existing JSON suffix."""
    filename = name if name.endswith(".json") else f"{name}.json"
    return directory / filename


class Explorer:
    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url.rstrip("/"), timeout=5.0)
        SAMPLES.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []

    def capture(self, name: str, response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError:
            body = {"text": response.text[:4000]}
        sample_path(name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
        self.records.append(
            {
                "name": name,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body_shape": body_shape(body),
            }
        )
        return body

    def request(
        self, method: str, path: str, name: str, **kwargs: Any
    ) -> tuple[httpx.Response, Any]:
        response = self.client.request(method, path, **kwargs)
        return response, self.capture(name, response)

    def get(self, path: str, name: str) -> Any:
        return self.request("GET", path, name)[1]

    def post(
        self, path: str, name: str, payload: dict[str, Any] | None = None
    ) -> tuple[httpx.Response, Any]:
        return self.request("POST", path, name, json=payload or {})

    def stream_sample(self, name: str = "stream") -> None:
        with self.client.stream("GET", "/v1/stream", timeout=3.0) as response:
            lines: list[str] = []
            for line in response.iter_lines():
                lines.append(line)
                if len(lines) >= 2:
                    break
            body = {"content_type": response.headers.get("content-type"), "lines": lines}
            sample_path(name).write_text(json.dumps(body, indent=2) + "\n")
            self.records.append(
                {
                    "name": name,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body_shape": body_shape(body),
                }
            )

    def reset_and_pause(self) -> None:
        self.post("/admin/reset", "admin-reset.json")
        self.post("/admin/pause", "admin-pause.json")

    def save_records(self, extra: dict[str, Any]) -> None:
        output = {"records": self.records, "measurements": extra}
        (SAMPLES / "exploration-results.json").write_text(json.dumps(output, indent=2) + "\n")


def explore(explorer: Explorer) -> dict[str, Any]:
    measurements: dict[str, Any] = {}
    faults_may_be_active = True
    try:
        explorer.reset_and_pause()

        paths = (
            ("/v1/health", "health"),
            ("/v1/instance", "instance"),
            ("/v1/regions", "regions"),
            ("/v1/depots", "depots"),
            ("/v1/stations", "stations"),
            ("/v1/routes", "routes"),
            ("/v1/supply-arrivals", "supply-arrivals"),
            ("/v1/events", "events"),
            ("/v1/allocations", "allocations"),
            ("/v1/demand-history?limit=2000", "demand-history"),
            ("/v1/metrics", "metrics"),
            ("/admin", "admin-console"),
            ("/admin/events", "admin-events"),
            ("/admin/faults", "admin-faults"),
            ("/admin/audit?limit=100", "admin-audit"),
        )
        bodies = {name: explorer.get(path, name) for path, name in paths}
        for name, _key in (("depots", "depots"), ("stations", "stations")):
            for entity in bodies[name]:
                suffix = entity["id"].split("-")[-1]
                explorer.get(f"/v1/{name}/{entity['id']}", f"{name[:-1]}-{suffix}-detail")
        explorer.stream_sample()

        for tick in range(1, 11):
            explorer.post("/admin/step", f"step-{tick:02d}.json")
        tick10 = explorer.get("/v1/instance", "instance-after-10-steps")
        measurements["after_10_steps"] = tick10

        explorer.reset_and_pause()
        routes = explorer.get("/v1/routes", "routes-before-allocation")
        route = routes[0]
        body = {
            "idempotency_key": "sprint1-explorer-replay",
            "source_depot_id": route["source_depot_id"],
            "destination_station_id": route["destination_station_id"],
            "route_id": route["id"],
            "fuel_type": "DIESEL",
            "quantity": 1,
        }
        created, allocation = explorer.post("/v1/allocations", "allocation-create.json", body)
        replay, replay_body = explorer.post("/v1/allocations", "allocation-replay.json", body)
        changed_body = dict(body, quantity=2)
        mismatch, mismatch_body = explorer.post(
            "/v1/allocations", "allocation-key-mismatch.json", changed_body
        )
        explorer.get("/v1/allocations", "allocations")
        measurements["allocation_replay"] = {
            "create_status": created.status_code,
            "replay_status": replay.status_code,
            "replay_same_allocation": allocation.get("id") == replay_body.get("id"),
            "different_body_status": mismatch.status_code,
            "different_body_code": (mismatch_body.get("detail") or {}).get("code"),
        }
        if (
            created.status_code in (200, 201)
            and isinstance(allocation, dict)
            and "id" in allocation
        ):
            explorer.post(f"/v1/allocations/{allocation['id']}/cancel", "allocation-cancel.json")

        for event_type in EVENT_TYPES:
            explorer.reset_and_pause()
            event_body = {
                "type": event_type,
                "start_tick": 1,
                "duration_ticks": 1,
                "parameters": {},
            }
            response, _ = explorer.post("/admin/events", f"event-{event_type}.json", event_body)
            step, _ = explorer.post("/admin/step", f"event-{event_type}-step.json")
            measurements.setdefault("event_statuses", {})[event_type] = {
                "inject_status": response.status_code,
                "step_status": step.status_code,
            }

        explorer.reset_and_pause()
        for _ in range(10):
            explorer.post("/admin/step", "past-event-advance.json")
        past_event, past_body = explorer.post(
            "/admin/events",
            "event-past-start-tick.json",
            {"type": "demand_spike", "start_tick": 0, "duration_ticks": 1, "parameters": {}},
        )
        past_event_step, _ = explorer.post("/admin/step", "event-past-start-step.json")
        current_events = explorer.get("/v1/events", "events")
        measurements["past_event"] = {
            "status": past_event.status_code,
            "body": past_body,
            "step_status": past_event_step.status_code,
            "status_after_step": current_events[0].get("status")
            if isinstance(current_events, list) and current_events
            else None,
            "current_tick": explorer.get("/v1/instance", "instance-after-past-event").get("tick"),
        }

        for fault_type in FAULT_TYPES:
            explorer.reset_and_pause()
            parameters = {"delay_ms": 500} if fault_type == "latency" else {}
            if fault_type == "error_rate":
                parameters = {"rate": 1.0}
            explorer.post(
                "/admin/faults",
                f"fault-{fault_type}-created.json",
                {"type": fault_type, "duration_seconds": 30, "parameters": parameters},
            )
            try:
                if fault_type == "stream_disconnect":
                    explorer.stream_sample("fault-stream_disconnect-response")
                else:
                    explorer.get("/v1/instance", f"fault-{fault_type}-response")
            finally:
                clear, clear_body = explorer.post(
                    "/admin/faults/clear", f"fault-{fault_type}-clear.json"
                )
                measurements.setdefault("fault_clear", {})[fault_type] = {
                    "status": clear.status_code,
                    "body": clear_body,
                }

        explorer.reset_and_pause()
        start = explorer.get("/v1/instance", "timing-start-instance")
        explorer.post("/admin/run", "admin-run.json")
        started = time.monotonic()
        time.sleep(1.25)
        elapsed = time.monotonic() - started
        explorer.post("/admin/pause", "admin-pause-after-timing.json")
        end = explorer.get("/v1/instance", "timing-end-instance")
        measurements["speed_probe"] = {
            "wall_seconds": elapsed,
            "ticks_advanced": end.get("tick", 0) - start.get("tick", 0),
            "observed_ticks_per_second": (end.get("tick", 0) - start.get("tick", 0)) / elapsed,
        }

        explorer.reset_and_pause()
        for index in range(96):
            explorer.post("/admin/step", f"demand-step-{index + 1:03d}.json")
        demand_history = explorer.get("/v1/demand-history?limit=2000", "demand-history")
        tick_minutes = explorer.get("/v1/instance", "instance-after-96-ticks").get("tick_minutes")
        measurements["demand_probe"] = {
            "ticks": 96,
            "tick_minutes": tick_minutes,
            "observations": len(demand_history) if isinstance(demand_history, list) else 0,
            "observations_by_station": {
                station: len([row for row in demand_history if row.get("station_id") == station])
                for station in sorted({row.get("station_id") for row in demand_history})
            }
            if isinstance(demand_history, list)
            else {},
            "mean_demand_by_station_fuel": summarize_demand(demand_history),
        }
        faults_may_be_active = False
        return measurements
    finally:
        if faults_may_be_active:
            try:
                explorer.post("/admin/faults/clear", "admin-faults-clear-final.json")
            except httpx.HTTPError:
                pass
        explorer.save_records(measurements)
        explorer.client.close()


def summarize_demand(rows: Any) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    if not isinstance(rows, list):
        return {}
    for row in rows:
        key = f"{row.get('station_id')}:{row.get('fuel_type')}"
        grouped.setdefault(key, []).append(float(row.get("demand_liters", 0)))
    return {key: round(statistics.fmean(values), 3) for key, values in sorted(grouped.items())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=__import__("os").environ.get("SIM_BASE_URL", "http://localhost:8000"),
    )
    args = parser.parse_args()
    explorer = Explorer(args.base_url)
    try:
        response = explorer.client.get("/v1/health")
    except httpx.HTTPError as exc:
        raise SystemExit(f"Simulator is not reachable at {args.base_url}: {exc}") from exc
    if response.status_code != 200:
        raise SystemExit(f"Simulator health returned HTTP {response.status_code}: {response.text}")
    measurements = explore(explorer)
    print(json.dumps(measurements, indent=2))


if __name__ == "__main__":
    main()
