from __future__ import annotations

import json
from pathlib import Path

from scripts.loadtest_report import render


def test_loadtest_report_uses_measured_values_and_marks_missing_metrics(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "workload": "read API",
                "stages": "10 users",
                "http_req_duration": {"avg": 12, "med": 10, "p(95)": 20, "p(99)": 30},
                "http_reqs": {"count": 50, "rate": 5},
                "request_errors": {"rate": 0},
            }
        )
    )

    report = render(summary)

    assert "| p95 latency (ms) | 20 |" in report
    assert "| Error rate | 0 |" in report
    assert "unavailable" in report
