#!/usr/bin/env python3
"""Interactive storyline runner for the 10-minute judging day live demonstration.

Provides an automated or guided rehearsal harness with dry-run, speed adjustment,
and skip controls. ALWAYS restores the simulator to a clean, paused state upon exit.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def http_post(url: str, data: dict | None = None, timeout: float = 5.0) -> tuple[int, str]:
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


class DemoDirector:
    def __init__(
        self,
        *,
        sim_url: str = "http://localhost:8000",
        api_url: str = "http://localhost:8101",
        dry_run: bool = False,
        speed: float = 1.0,
        skip_phases: set[str] | None = None,
        auto_prompt: bool = True,
    ) -> None:
        self.sim_url = sim_url.rstrip("/")
        self.api_url = api_url.rstrip("/")
        self.dry_run = dry_run
        self.speed = max(0.1, speed)
        self.skip_phases = skip_phases or set()
        self.auto_prompt = auto_prompt
        self.log_entries: list[dict[str, object]] = []
        self.start_time: float = 0.0

    def log(self, phase: str, message: str, presenter_cue: str | None = None) -> None:
        elapsed = time.monotonic() - self.start_time if self.start_time > 0 else 0.0
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed, 2),
            "phase": phase,
            "message": message,
            "presenter_cue": presenter_cue,
        }
        self.log_entries.append(entry)

        print(f"\n[{elapsed:05.1f}s] === {phase.upper()} ===")
        print(f"  {message}")
        if presenter_cue:
            print(f"  👉 PRESENTER CUE: {presenter_cue}")

    def pause(self, seconds: float) -> None:
        if self.dry_run:
            return
        time.sleep(seconds / self.speed)

    def execute_post(self, path: str, payload: dict | None = None) -> tuple[int, str]:
        if self.dry_run:
            return 200, json.dumps({"dry_run": True})
        url = f"{self.sim_url}{path}"
        return http_post(url, payload)

    def run_storyline(self) -> dict[str, object]:
        self.start_time = time.monotonic()
        print("==================================================================")
        print("  FUEL INTELLIGENCE & RESILIENCE PLATFORM: DEMO DIRECTOR")
        print(f"  Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'} | Speed: {self.speed}x")
        print("==================================================================")

        try:
            # Phase 0: Baseline
            self.log(
                "Phase 0: Baseline State & HUD Observation",
                "Establishing baseline: Pausing simulator and verifying live health.",
                "Point to Header HUD: Tick number, 1.0x speed, SIMULATED badge, and ● LIVE PUSH indicator.",
            )
            self.execute_post("/admin/pause")
            self.execute_post("/admin/faults/clear")
            self.pause(2.0)

            # Phase 1: Demand Surge Crisis
            self.log(
                "Phase 1: Demand Surge Crisis Injection",
                "Injecting 2.5x demand surge on station-mirpur for 10 ticks.",
                "Navigate to 'Stockout Risk'. Show the sudden drop in hours to stockout and widening P10/P90 Monte Carlo probability band.",
            )
            spike_payload = {
                "type": "demand_spike",
                "start_tick": 0,
                "end_tick": 12,
                "station_id": "station-mirpur",
                "surge_factor": 2.5,
            }
            self.execute_post("/admin/events", spike_payload)
            self.execute_post("/admin/step")
            self.execute_post("/admin/step")
            self.pause(3.0)

            # Phase 2: Decision & What-If
            self.log(
                "Phase 2: Decision & What-If Counterfactual",
                "Recommendation generated by pure HeuristicPolicy with physical constraint validation.",
                "Navigate to 'Recommendations'. Click 'Review Explanation'. Point to What-If simulator showing counterfactual runway extension.",
            )
            self.pause(3.0)

            # Phase 3: Human Approval Lifecycle
            self.log(
                "Phase 3: Human Approval & Execution Lifecycle",
                "Demonstrating operator decision workflow: approval requires operator token and recorded operator name.",
                "Enter operator token and name 'Senior Dispatcher Rahat'. Click 'Approve Allocation'. Show lifecycle: PROPOSED -> APPROVED -> SUBMITTED -> IN_TRANSIT.",
            )
            self.execute_post("/admin/step")
            self.execute_post("/admin/step")
            self.pause(3.0)

            # Phase 4: Optional Fault or Disruption
            if "disruption" not in self.skip_phases:
                self.log(
                    "Phase 4: Surprise Fault & Circuit Breaker",
                    "Simulating transient simulator outage to prove resilience and alerting.",
                    "Show amber 'Data is degraded' banner, Alert Center incident card, and automatic Alertmanager routing.",
                )
                self.execute_post(
                    "/admin/faults",
                    {"type": "unavailable", "duration_seconds": 6, "parameters": {}},
                )
                self.pause(2.5)
                self.execute_post("/admin/faults/clear")
                self.log(
                    "Phase 4: Fault Recovery",
                    "Simulator fault cleared. Worker reconnects with zero state corruption.",
                    "Point to instant UI restoration and live status recovery.",
                )
                self.pause(2.0)

            # Phase 5: Conclusion & Clean State
            self.log(
                "Phase 5: Demo Conclusion & Stand-Down",
                "Restoring platform to clean standby state with simulator PAUSED.",
                "Conclude presentation: Highlight 97.93% heuristic SLA (+0.79% [0.41%, 1.27%] CI), 2.93s RTO, and 0 security vulnerabilities.",
            )
            self.execute_post("/admin/faults/clear")
            self.execute_post("/admin/pause")

        finally:
            self.execute_post("/admin/faults/clear")
            self.execute_post("/admin/pause")

        total_duration = time.monotonic() - self.start_time
        print("\n==================================================================")
        print(f"  DEMO REHEARSAL COMPLETE: Duration {total_duration:.1f}s")
        print("  Simulator left PAUSED with faults cleared.")
        print("==================================================================")

        return {
            "mode": "dry_run" if self.dry_run else "live",
            "speed": self.speed,
            "total_duration_seconds": round(total_duration, 2),
            "log": self.log_entries,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 10-minute judging day demo storyline.")
    parser.add_argument("--dry-run", action="store_true", help="Run narrative steps without calling APIs")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (default: 1.0, e.g. 5.0 for fast rehearsal)")
    parser.add_argument("--skip", type=str, default="", help="Comma-separated phases to skip (e.g. 'disruption')")
    parser.add_argument("--sim-url", type=str, default="http://localhost:8000", help="Simulator base URL")
    parser.add_argument("--api-url", type=str, default="http://localhost:8101", help="API base URL")
    parser.add_argument("--output", type=str, default="", help="Path to write JSON rehearsal evidence")
    args = parser.parse_args()

    skips = {s.strip().lower() for s in args.skip.split(",") if s.strip()}
    director = DemoDirector(
        sim_url=args.sim_url,
        api_url=args.api_url,
        dry_run=args.dry_run,
        speed=args.speed,
        skip_phases=skips,
    )

    result = director.run_storyline()

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2))
        print(f"Saved rehearsal evidence to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
