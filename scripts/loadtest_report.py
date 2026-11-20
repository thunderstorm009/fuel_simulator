#!/usr/bin/env python3
"""Render a measured k6 JSON summary; missing fields remain explicitly unavailable."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def render(path: Path) -> str:
    data: dict[str, Any] = json.loads(path.read_text())
    duration = data.get("http_req_duration", {})
    requests = data.get("http_reqs", {})
    errors = data.get("request_errors", {})
    return "\n".join(
        [
            "# Load test results",
            "",
            f"Source: `{path}`",
            f"Workload: {data.get('workload', 'not recorded')}",
            f"Stages: {data.get('stages', 'not recorded')}",
            "",
            "| Measure | Value |",
            "|---|---:|",
            f"| Requests | {requests.get('count', 'unavailable')} |",
            f"| Throughput (req/s) | {requests.get('rate', 'unavailable')} |",
            f"| Average latency (ms) | {duration.get('avg', 'unavailable')} |",
            f"| p50 latency (ms) | {duration.get('med', 'unavailable')} |",
            f"| p95 latency (ms) | {duration.get('p(95)', 'unavailable')} |",
            f"| p99 latency (ms) | {duration.get('p(99)', 'unavailable')} |",
            f"| Error rate | {errors.get('rate', 'unavailable')} |",
            "",
            "Repeat normal, simulator-latency, and predictor-unavailable runs. "
            "Keep raw summaries beside the report.",
            "",
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/loadtest_report.py <k6-summary.json>")
    print(render(Path(sys.argv[1])))
