from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("webhook-receiver")

LOG_PATH = Path("/logs/alerts.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

RECEIVED_ALERTS: list[dict[str, Any]] = []


class AlertHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"webhook-receiver"}')
            return

        if self.path == "/alerts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"alerts": RECEIVED_ALERTS}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/clear":
            RECEIVED_ALERTS.clear()
            if LOG_PATH.exists():
                LOG_PATH.unlink()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"cleared"}')
            return

        if self.path in ("/webhook", "/", ""):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as exc:
                logger.error("Failed to parse webhook JSON: %s", exc)
                self.send_response(400)
                self.end_headers()
                return

            now_iso = datetime.now(timezone.utc).isoformat()
            status = payload.get("status", "unknown")
            alerts = payload.get("alerts", [])
            logger.info("Received Alertmanager webhook: status=%s, count=%d", status, len(alerts))

            for alert in alerts:
                labels = alert.get("labels", {})
                annotations = alert.get("annotations", {})
                entry = {
                    "received_at": now_iso,
                    "status": alert.get("status", status),
                    "alertname": labels.get("alertname", "unknown"),
                    "severity": labels.get("severity", "unknown"),
                    "summary": annotations.get("summary", ""),
                    "description": annotations.get("description", ""),
                    "runbook_url": annotations.get("runbook_url", ""),
                    "starts_at": alert.get("startsAt", ""),
                    "ends_at": alert.get("endsAt", ""),
                    "raw": alert,
                }
                RECEIVED_ALERTS.append(entry)
                logger.info(
                    "ALERT [%s]: %s (severity=%s) - %s (runbook: %s)",
                    entry["status"].upper(),
                    entry["alertname"],
                    entry["severity"],
                    entry["summary"],
                    entry["runbook_url"],
                )
                try:
                    with LOG_PATH.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(entry) + "\n")
                except Exception as err:
                    logger.warning("Could not write to log file: %s", err)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"accepted"}')
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy default BaseHTTPRequestHandler access logging
        pass


def main() -> None:
    port = 5001
    server = HTTPServer(("0.0.0.0", port), AlertHandler)
    logger.info("Webhook receiver listening on 0.0.0.0:%d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Webhook receiver stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
