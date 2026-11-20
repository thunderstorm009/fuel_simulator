#!/usr/bin/env bash
set -euo pipefail

SIM_BASE_URL="${SIM_BASE_URL:-http://localhost:8000}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8101}"
PREDICTOR_BASE_URL="${PREDICTOR_BASE_URL:-http://localhost:8103}"
WAIT_SECONDS="${WAIT_SECONDS:-8}"
fault_active=0

clear_fault() {
  if (( fault_active )); then
    curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/faults/clear" >/dev/null || true
    fault_active=0
  fi
}
trap clear_fault EXIT INT TERM

scene() {
  local fault="$1" params="$2"
  echo "Scene: $fault. Expected UI: simulator data health/banner reflects stale or degraded data; cached values remain visible."
  curl --fail --silent --show-error -H 'Content-Type: application/json' \
    -d "{\"type\":\"$fault\",\"duration_seconds\":30,\"parameters\":$params}" \
    "$SIM_BASE_URL/admin/faults"
  fault_active=1
  sleep "$WAIT_SECONDS"
  curl --silent --show-error "$API_BASE_URL/api/data-health" || true
  clear_fault
  echo "Recovery requested for $fault; allow the worker to complete its next REST refresh."
}

for fault in unavailable error_rate latency stale_data stream_disconnect; do
  case "$fault" in
    error_rate) params='{"rate":1.0}' ;;
    latency) params='{"delay_ms":500}' ;;
    *) params='{}' ;;
  esac
  scene "$fault" "$params"
done

echo 'Scene: malformed simulator data. Use a test-only malformed response fixture; do not alter simulator state.'
echo 'Expected UI: last good snapshot retained; snapshot rejection is logged and counted.'
echo 'Automated malformed-data coverage: tests/integration/test_resilience.py'

echo 'Scene: predictor unavailable. Expected UI: review-required baseline forecast; fallback metric and incident increase.'
if command -v docker >/dev/null 2>&1; then
  echo 'Run `docker compose stop predictor`, observe /api/health and worker metrics, then `docker compose start predictor`.'
else
  echo 'Docker unavailable; skip predictor stop/recovery.'
fi
