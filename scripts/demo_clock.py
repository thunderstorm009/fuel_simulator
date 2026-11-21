#!/usr/bin/env python3
"""Controllable demo clock stepping the simulator via /admin/step at a chosen rate.

Allows operators and judges to observe platform behavior at controlled speeds
(e.g., 0.5 ticks/second = 1 tick every 2 seconds).
Ensures the simulator is paused cleanly on exit.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
import urllib.error
import urllib.request


def http_post(url: str, timeout: float = 5.0) -> dict | None:
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else {}
    except Exception as exc:
        print(f"[demo_clock] POST {url} failed: {exc}", file=sys.stderr)
        return None


def http_get(url: str, timeout: float = 5.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else {}
    except Exception as exc:
        print(f"[demo_clock] GET {url} failed: {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Step simulator clock at a controlled rate.")
    parser.add_argument("--rate", type=float, default=0.5, help="Ticks per second (default: 0.5)")
    parser.add_argument(
        "--ticks", type=int, default=0, help="Total ticks to advance (0 for infinite)"
    )
    parser.add_argument(
        "--sim-url", type=str, default="http://localhost:8000", help="Simulator base URL"
    )
    args = parser.parse_args()

    sim_url = args.sim_url.rstrip("/")
    rate = max(0.01, args.rate)
    delay_s = 1.0 / rate

    # Check simulator reachability
    inst = http_get(f"{sim_url}/v1/instance")
    if inst is None:
        print(f"[demo_clock] Simulator unreachable at {sim_url}", file=sys.stderr)
        return 1

    # Ensure simulator is PAUSED so demo_clock controls stepping
    http_post(f"{sim_url}/admin/pause")
    print(
        f"[demo_clock] Simulator paused. Stepping at {rate:.2f} ticks/s "
        f"(interval: {delay_s:.2f}s)..."
    )
    print("[demo_clock] Press Ctrl+C to stop stepping (simulator will remain PAUSED).")

    running = True

    def handle_signal(sig, frame):
        nonlocal running
        print("\n[demo_clock] Received interrupt. Halting clock...")
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    step_count = 0
    start_time = time.time()

    while running:
        t0 = time.time()
        res = http_post(f"{sim_url}/admin/step")
        step_count += 1

        if res and "tick" in res:
            tick_num = res["tick"]
            sim_time = res.get("sim_time", "")
            print(f"[demo_clock] Step {step_count}: tick={tick_num} sim_time={sim_time}")
        else:
            print(f"[demo_clock] Step {step_count} completed")

        if args.ticks > 0 and step_count >= args.ticks:
            print(f"[demo_clock] Reached target tick count ({args.ticks}).")
            break

        elapsed = time.time() - t0
        sleep_time = max(0.0, delay_s - elapsed)
        if running and sleep_time > 0:
            time.sleep(sleep_time)

    # Clean exit: ensure simulator is paused
    http_post(f"{sim_url}/admin/pause")
    total_time = time.time() - start_time
    actual_rate = step_count / max(0.001, total_time)
    print(
        f"[demo_clock] Completed {step_count} ticks in {total_time:.1f}s "
        f"({actual_rate:.2f} ticks/s). Simulator left PAUSED."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
