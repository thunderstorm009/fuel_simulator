#!/usr/bin/env python3
"""Demonstrate end-to-end alert routing through Alertmanager to local webhook receiver."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("alert-demo")

EVIDENCE_JSON = Path("docs/evidence/day-4/alert-routing-evidence.json")
EVIDENCE_TXT = Path("docs/evidence/day-4/alert-routing-evidence.txt")


def http_request(
    url: str,
    payload: dict[str, Any] | None = None,
    method: str | None = None,
    timeout: float = 5.0,
) -> tuple[int, str]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def wait_for_service(url: str, name: str, timeout_seconds: float = 30.0) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < timeout_seconds:
        status, _ = http_request(url, timeout=2.0)
        if 200 <= status < 300:
            logger.info("Service %s is healthy at %s", name, url)
            return True
        time.sleep(1.0)
    logger.error("Service %s timed out waiting for health at %s", name, url)
    return False


def run_cmd(cmd: list[str]) -> str:
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return res.stdout.strip()


def main() -> int:
    logger.info("Starting Alertmanager and Webhook receiver under profile 'alerts'")
    run_cmd(
        [
            "docker",
            "compose",
            "--profile",
            "alerts",
            "up",
            "-d",
            "--build",
            "alertmanager",
            "webhook-receiver",
        ]
    )
    run_cmd(["docker", "compose", "restart", "prometheus"])

    if not wait_for_service("http://localhost:9093/-/healthy", "Alertmanager"):
        return 1
    if not wait_for_service("http://localhost:5001/health", "Webhook-Receiver"):
        return 1
    if not wait_for_service("http://localhost:9090/-/healthy", "Prometheus"):
        return 1

    # Wait for Prometheus to discover Alertmanager
    start_disc = time.monotonic()
    am_discovered = False
    while time.monotonic() - start_disc < 20.0:
        _, am_resp = http_request("http://localhost:9090/api/v1/alertmanagers")
        try:
            active_ams = json.loads(am_resp).get("data", {}).get("activeAlertmanagers", [])
            if len(active_ams) > 0:
                logger.info("Prometheus connected to Alertmanager at %s", active_ams[0]["url"])
                am_discovered = True
                break
        except Exception:
            pass
        time.sleep(1.0)

    if not am_discovered:
        logger.error("Prometheus failed to discover Alertmanager")
        return 1

    # Clear prior webhook alerts
    http_request("http://localhost:5001/clear", payload={}, method="POST")

    # Clear simulator faults to establish clean baseline
    http_request("http://localhost:8000/admin/faults/clear", payload={}, method="POST")
    time.sleep(3.0)

    evidence_records: list[dict[str, Any]] = []

    # 1. Baseline check
    _, body = http_request("http://localhost:5001/alerts")
    baseline_alerts = json.loads(body).get("alerts", [])
    logger.info("Baseline alerts count: %d", len(baseline_alerts))

    # 2. Inject fault: unavailable
    fault_type = "unavailable"
    inject_time = datetime.now(timezone.utc).isoformat()
    logger.info("Injecting simulator fault: %s at %s", fault_type, inject_time)
    code, resp_body = http_request(
        "http://localhost:8000/admin/faults",
        payload={"type": fault_type, "duration_seconds": 120, "parameters": {}},
        method="POST",
    )
    logger.info("Fault injected (status %d): %s", code, resp_body)

    # 3. Wait for alert to fire and be received by webhook
    firing_alert: dict[str, Any] | None = None
    wait_start = time.monotonic()
    logger.info("Waiting for firing alert to arrive at webhook-receiver...")
    while time.monotonic() - wait_start < 90.0:
        _, body = http_request("http://localhost:5001/alerts")
        try:
            alerts = json.loads(body).get("alerts", [])
            for a in alerts:
                if a.get("status") == "firing":
                    firing_alert = a
                    break
            if firing_alert:
                break
        except Exception:
            pass
        time.sleep(2.0)

    if not firing_alert:
        logger.error("Failed to receive firing alert within 90s")
        http_request("http://localhost:8000/admin/faults/clear", payload={}, method="POST")
        return 1

    logger.info(
        "RECEIVED FIRING ALERT: %s (severity=%s) at %s",
        firing_alert["alertname"],
        firing_alert["severity"],
        firing_alert["received_at"],
    )
    logger.info("Runbook link: %s", firing_alert["runbook_url"])
    evidence_records.append({"step": "alert_fired", "alert": firing_alert})

    # 4. Clear fault
    clear_time = datetime.now(timezone.utc).isoformat()
    logger.info("Clearing simulator faults at %s", clear_time)
    code, resp_body = http_request(
        "http://localhost:8000/admin/faults/clear", payload={}, method="POST"
    )
    logger.info("Fault cleared (status %d): %s", code, resp_body)

    # 5. Wait for alert resolution to be delivered to webhook
    resolved_alert: dict[str, Any] | None = None
    wait_start = time.monotonic()
    logger.info("Waiting for resolution notification to arrive at webhook-receiver...")
    while time.monotonic() - wait_start < 90.0:
        _, body = http_request("http://localhost:5001/alerts")
        try:
            alerts = json.loads(body).get("alerts", [])
            for a in alerts:
                if (
                    a.get("status") == "resolved"
                    and a.get("alertname") == firing_alert["alertname"]
                ):
                    resolved_alert = a
                    break
            if resolved_alert:
                break
        except Exception:
            pass
        time.sleep(2.0)

    if not resolved_alert:
        logger.error("Failed to receive resolved alert notification within 90s")
        return 1

    logger.info(
        "RECEIVED RESOLVED ALERT: %s at %s",
        resolved_alert["alertname"],
        resolved_alert["received_at"],
    )
    evidence_records.append({"step": "alert_resolved", "alert": resolved_alert})

    # 6. Save evidence files
    summary_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fault_injected": fault_type,
        "fault_injected_at": inject_time,
        "fault_cleared_at": clear_time,
        "firing_alert": firing_alert,
        "resolved_alert": resolved_alert,
        "round_trip_seconds": (
            datetime.fromisoformat(resolved_alert["received_at"])
            - datetime.fromisoformat(firing_alert["received_at"])
        ).total_seconds(),
        "verified": True,
    }

    EVIDENCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    with EVIDENCE_TXT.open("w", encoding="utf-8") as f:
        f.write("=== END-TO-END ALERT ROUTING EVIDENCE ===\n")
        f.write(f"Timestamp: {summary_data['timestamp']}\n")
        f.write(f"Fault injected: {fault_type} at {inject_time}\n")
        f.write(
            f"FIRING alert received at: {firing_alert['received_at']}\n"
            f"  - Alertname: {firing_alert['alertname']}\n"
            f"  - Severity: {firing_alert['severity']}\n"
            f"  - Summary: {firing_alert['summary']}\n"
            f"  - Description: {firing_alert['description']}\n"
            f"  - Runbook URL: {firing_alert['runbook_url']}\n"
        )
        f.write(f"Fault cleared at: {clear_time}\n")
        f.write(
            f"RESOLVED alert received at: {resolved_alert['received_at']}\n"
            f"  - Alertname: {resolved_alert['alertname']}\n"
            f"  - Ends At: {resolved_alert['ends_at']}\n"
        )
        f.write(f"Resolution duration: {summary_data['round_trip_seconds']:.1f}s\n")
        f.write(
            "Status: PASS — End-to-end routing verified from "
            "Prometheus -> Alertmanager -> Webhook.\n"
        )

    logger.info("Evidence written to %s and %s", EVIDENCE_JSON, EVIDENCE_TXT)

    # 7. Cleanup alerts containers to preserve default compose posture
    logger.info("Stopping alerts profile containers (alertmanager, webhook-receiver)")
    run_cmd(
        [
            "docker",
            "compose",
            "--profile",
            "alerts",
            "stop",
            "alertmanager",
            "webhook-receiver",
        ]
    )

    # Ensure simulator paused with clean faults
    http_request("http://localhost:8000/admin/faults/clear", payload={}, method="POST")
    http_request("http://localhost:8000/admin/pause", payload={}, method="POST")

    print("\nSUCCESS: Alert routing drill completed cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
