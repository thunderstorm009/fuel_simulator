#!/usr/bin/env python3
"""Inject reversible simulator API faults and record API availability."""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

FAULTS = ("unavailable", "error_rate", "latency", "stale_data", "stream_disconnect")


def request(
    url: str,
    payload: dict | None = None,
    method: str | None = None,
    timeout: float = 3.0,
) -> tuple[int, str]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=2)
    parser.add_argument("--sim-url", default="http://localhost:8000")
    parser.add_argument("--api-url", default="http://localhost:8101")
    parser.add_argument("--seed", type=int, default=20261120)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    stop_at = time.monotonic() + args.minutes * 60
    rows: list[dict[str, object]] = []
    try:
        while time.monotonic() < stop_at:
            fault = rng.choice(FAULTS)
            parameters = (
                {"rate": 1.0}
                if fault == "error_rate"
                else ({"delay_ms": 250} if fault == "latency" else {})
            )
            code, body = request(
                f"{args.sim_url}/admin/faults",
                {"type": fault, "duration_seconds": 8, "parameters": parameters},
            )
            rows.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "event": "inject",
                    "fault": fault,
                    "status": code,
                    "body": body,
                }
            )
            time.sleep(3)
            health_code, health_body = request(f"{args.api_url}/api/health")
            rows.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "event": "health",
                    "status": health_code,
                    "body": health_body,
                }
            )
            time.sleep(5)
            clear_code, clear_body = request(f"{args.sim_url}/admin/faults/clear", method="POST")
            rows.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "event": "clear",
                    "fault": fault,
                    "status": clear_code,
                    "body": clear_body,
                }
            )
            if health_code >= 500:
                raise RuntimeError(
                    f"API returned {health_code} outside the injected simulator fault"
                )
    finally:
        request(f"{args.sim_url}/admin/faults/clear", method="POST")
        print(json.dumps({"seed": args.seed, "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
