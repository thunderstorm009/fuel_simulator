#!/usr/bin/env python3
"""Execute k6 load test sweep across VU levels with container telemetry sampling."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
K6_SCRIPT = ROOT_DIR / "loadtest" / "k6.js"


def sample_stats(stop_event: threading.Event, samples: list[dict]):
    while not stop_event.is_set():
        try:
            res = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{.Name}},{{.CPUPerc}},{{.MemUsage}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) >= 3 and parts[0].startswith("fuel_simulator"):
                    name = parts[0].replace("fuel_simulator-", "").rsplit("-", 1)[0]
                    cpu = float(parts[1].replace("%", "").strip() or 0.0)
                    mem_str = parts[2].split("/")[0].strip()
                    if "GiB" in mem_str:
                        mem = float(mem_str.replace("GiB", "").strip()) * 1024
                    elif "MiB" in mem_str:
                        mem = float(mem_str.replace("MiB", "").strip())
                    elif "KiB" in mem_str:
                        mem = float(mem_str.replace("KiB", "").strip()) / 1024
                    else:
                        mem = 0.0
                    samples.append({"name": name, "cpu": cpu, "mem_mib": mem})
        except Exception:
            pass
        time.sleep(1.0)


def run_vu_stage(vus: int, duration_sec: int = 15) -> dict:
    summary_file = Path(f"/tmp/k6-summary-{vus}.json")
    if summary_file.exists():
        summary_file.unlink()

    stop_event = threading.Event()
    stats_samples: list[dict] = []
    stats_thread = threading.Thread(target=sample_stats, args=(stop_event, stats_samples))
    stats_thread.daemon = True
    stats_thread.start()

    cmd = [
        "k6",
        "run",
        "--vus",
        str(vus),
        "--duration",
        f"{duration_sec}s",
        str(K6_SCRIPT),
        "--summary-export",
        str(summary_file),
    ]

    print(f"--> Running k6: {vus} VUs for {duration_sec}s...")
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    _ = time.time() - t0
    stop_event.set()
    stats_thread.join(timeout=3.0)

    if not summary_file.exists():
        print(f"Error: summary file not created for {vus} VUs: {res.stderr}", file=sys.stderr)
        return {"vus": vus, "error": res.stderr}

    with open(summary_file, encoding="utf-8") as f:
        data = json.load(f)

    metrics = data.get("metrics", {})
    reqs_count = metrics.get("http_reqs", {}).get("count", 0)
    throughput = metrics.get("http_reqs", {}).get("rate", 0.0)
    error_rate = metrics.get("request_errors", {}).get("rate", 0.0) * 100.0

    dur = metrics.get("request_duration_ms", {})
    p50 = dur.get("med", 0.0)
    p95 = dur.get("p(95)", 0.0)
    p99 = dur.get("max", 0.0)  # k6 default summary exports med, p(90), p(95), max

    whatif_dur = metrics.get("whatif_duration_ms", {})
    whatif_p50 = whatif_dur.get("med", 0.0)
    whatif_p95 = whatif_dur.get("p(95)", 0.0)

    # Calculate peak container telemetry
    api_cpu = max([s["cpu"] for s in stats_samples if s["name"] == "api"] or [0.0])
    api_mem = max([s["mem_mib"] for s in stats_samples if s["name"] == "api"] or [0.0])
    pg_cpu = max([s["cpu"] for s in stats_samples if s["name"] == "postgres"] or [0.0])
    pg_mem = max([s["mem_mib"] for s in stats_samples if s["name"] == "postgres"] or [0.0])

    return {
        "vus": vus,
        "requests": reqs_count,
        "throughput_rps": round(throughput, 1),
        "error_rate_pct": round(error_rate, 2),
        "read_p50_ms": round(p50, 1),
        "read_p95_ms": round(p95, 1),
        "read_p99_ms": round(p99, 1),
        "whatif_p50_ms": round(whatif_p50, 1),
        "whatif_p95_ms": round(whatif_p95, 1),
        "api_cpu_pct": round(api_cpu, 1),
        "api_mem_mib": round(api_mem, 1),
        "pg_cpu_pct": round(pg_cpu, 1),
        "pg_mem_mib": round(pg_mem, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Run k6 VU load test sweep")
    parser.add_argument("--vus", nargs="+", type=int, default=[10, 50, 100, 200, 400])
    parser.add_argument("--duration", type=int, default=12)
    parser.add_argument("--out", type=Path, default=ROOT_DIR / "docs" / "results" / "k6-sweep.json")
    args = parser.parse_args()

    results = []
    print(f"Starting k6 sweep across VUs: {args.vus}")
    for v in args.vus:
        row = run_vu_stage(v, duration_sec=args.duration)
        results.append(row)
        print(
            f"Result {v} VUs: {row.get('throughput_rps')} req/s | "
            f"Read p95: {row.get('read_p95_ms')}ms | WhatIf p95: {row.get('whatif_p95_ms')}ms | "
            f"Errors: {row.get('error_rate_pct')}%"
        )
        time.sleep(2)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote results to {args.out}")

    # Output formatted markdown table
    hdr = (
        "| VUs | Requests | Throughput (req/s) | Read p50 (ms) | Read p95 (ms) | "
        "WhatIf p95 (ms) | Errors | API CPU | API Mem | PG CPU | PG Mem |"
    )
    print(f"\n{hdr}")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        print(
            f"| **{r['vus']}** | {r['requests']} | {r['throughput_rps']} | "
            f"{r['read_p50_ms']} | {r['read_p95_ms']} | {r['whatif_p50_ms']} | "
            f"{r['error_rate_pct']}% | {r['api_cpu_pct']}% | {r['api_mem_mib']} MiB | "
            f"{r['pg_cpu_pct']}% | {r['pg_mem_mib']} MiB |"
        )


if __name__ == "__main__":
    main()
