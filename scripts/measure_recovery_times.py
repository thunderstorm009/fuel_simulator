#!/usr/bin/env python3
"""Measure service recovery times:
1. Time until container is 'running'
2. Time until container is 'healthy'
3. Time until fresh data is visible in the UI or API
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SERVICES = [
    {
        "name": "postgres",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:8101/api/state", timeout=2),
    },
    {
        "name": "api",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:8101/api/state", timeout=2),
    },
    {
        "name": "worker",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:8102/health", timeout=2),
    },
    {
        "name": "predictor",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:8103/health", timeout=2),
    },
    {
        "name": "frontend",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:5173/", timeout=2),
    },
    {
        "name": "prometheus",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:9090/-/healthy", timeout=2),
    },
    {
        "name": "grafana",
        "probe": lambda: urllib.request.urlopen("http://127.0.0.1:3000/api/health", timeout=2),
    },
]


def inspect_container(service: str) -> dict[str, str]:
    cmd = [
        "docker",
        "compose",
        "-f",
        str(REPO_ROOT / "docker-compose.yml"),
        "ps",
        service,
        "--format",
        "json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    output = res.stdout.strip()
    if not output:
        return {"State": "unknown", "Health": "unknown"}
    try:
        data = json.loads(output)
        if isinstance(data, list):
            data = data[0] if data else {}
        return {
            "State": data.get("State", "").lower(),
            "Health": data.get("Health", "").lower(),
        }
    except Exception:
        return {"State": "unknown", "Health": "unknown"}


def measure_service(service_cfg: dict) -> dict[str, float]:
    service = service_cfg["name"]
    probe_fn = service_cfg["probe"]

    print(f"--> Restarting {service}...")
    t0 = time.monotonic()
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(REPO_ROOT / "docker-compose.yml"),
            "restart",
            service,
        ],
        capture_output=True,
        check=True,
    )

    t_running = None
    t_healthy = None
    t_data = None

    deadline = t0 + 40.0
    while time.monotonic() < deadline:
        now = time.monotonic()
        st = inspect_container(service)
        state = st.get("State", "")
        health = st.get("Health", "")

        if t_running is None and state == "running":
            t_running = now - t0

        if t_healthy is None:
            # If health is available and healthy, or if no healthcheck defined and running
            if health == "healthy" or (state == "running" and health in ("", "none")):
                t_healthy = now - t0

        if t_data is None:
            try:
                res = probe_fn()
                if res.status == 200:
                    t_data = now - t0
            except Exception:
                pass

        if t_running is not None and t_healthy is not None and t_data is not None:
            break
        time.sleep(0.2)

    t_running = t_running or (time.monotonic() - t0)
    t_healthy = t_healthy or (time.monotonic() - t0)
    t_data = t_data or (time.monotonic() - t0)

    print(
        f"    {service}: Running {t_running:.2f}s | "
        f"Healthy {t_healthy:.2f}s | Data visible {t_data:.2f}s"
    )
    return {
        "service": service,
        "running_seconds": round(t_running, 2),
        "healthy_seconds": round(t_healthy, 2),
        "data_visible_seconds": round(t_data, 2),
    }


def measure_full_stack() -> dict[str, float]:
    print("\n--> Measuring Full Stack Restart...")
    t0 = time.monotonic()
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(REPO_ROOT / "docker-compose.yml"),
            "restart",
        ],
        capture_output=True,
        check=True,
    )

    t_running = None
    t_healthy = None
    t_data = None

    deadline = t0 + 60.0
    while time.monotonic() < deadline:
        now = time.monotonic()
        all_running = True
        all_healthy = True

        for s in SERVICES:
            st = inspect_container(s["name"])
            if st.get("State", "") != "running":
                all_running = False
            health = st.get("Health", "")
            if health not in ("healthy", "", "none"):
                all_healthy = False

        if t_running is None and all_running:
            t_running = now - t0
        if t_healthy is None and all_healthy and all_running:
            t_healthy = now - t0

        if t_data is None:
            try:
                r1 = urllib.request.urlopen("http://127.0.0.1:8101/api/state", timeout=2)
                r2 = urllib.request.urlopen("http://127.0.0.1:5173/", timeout=2)
                if r1.status == 200 and r2.status == 200:
                    t_data = now - t0
            except Exception:
                pass

        if t_running is not None and t_healthy is not None and t_data is not None:
            break
        time.sleep(0.5)

    t_running = t_running or (time.monotonic() - t0)
    t_healthy = t_healthy or (time.monotonic() - t0)
    t_data = t_data or (time.monotonic() - t0)

    print(
        f"    Full stack: All Running {t_running:.2f}s | "
        f"All Healthy {t_healthy:.2f}s | Data visible {t_data:.2f}s"
    )
    return {
        "service": "full_stack",
        "running_seconds": round(t_running, 2),
        "healthy_seconds": round(t_healthy, 2),
        "data_visible_seconds": round(t_data, 2),
    }


def main() -> int:
    results = []
    print("=" * 60)
    print("MEASURING PER-SERVICE AND FULL STACK RECOVERY TIMES")
    print("=" * 60)

    for s in SERVICES:
        results.append(measure_service(s))
        time.sleep(1.0)

    full_res = measure_full_stack()
    results.append(full_res)

    out_file = REPO_ROOT / "docs" / "results" / "recovery-times.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nWrote recovery measurements to {out_file}")

    print("\n| Service | Container Running | Healthy | Data Visible in UI/API |")
    print("|---|---:|---:|---:|")
    for r in results:
        svc = r["service"]
        run_s = f"{r['running_seconds']:.2f}s"
        hlth_s = f"{r['healthy_seconds']:.2f}s"
        data_s = f"{r['data_visible_seconds']:.2f}s"
        print(f"| **{svc}** | {run_s} | {hlth_s} | {data_s} |")

    return 0


if __name__ == "__main__":
    sys.exit(main())
