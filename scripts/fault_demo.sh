#!/usr/bin/env bash
set -euo pipefail

SIM_BASE_URL="${SIM_BASE_URL:-http://localhost:8000}"
API_BASE_URL="${API_BASE_URL:-http://localhost:8101}"
WORKER_BASE_URL="${WORKER_BASE_URL:-http://localhost:8102}"
FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:5174}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FAULT_SECONDS="${FAULT_SECONDS:-60}"
WAIT_SECONDS="${WAIT_SECONDS:-18}"
fault_active=0
predictor_stopped=0
worker_stopped=0

clear_fault() {
  if (( fault_active )); then
    curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/faults/clear" >/dev/null
    fault_active=0
  fi
}

recover_services() {
  if (( worker_stopped )); then
    docker compose start worker >/dev/null
    worker_stopped=0
  fi
  if (( predictor_stopped )); then
    docker compose start predictor >/dev/null
    predictor_stopped=0
  fi
}

cleanup() {
  clear_fault || true
  recover_services || true
}
trap cleanup EXIT INT TERM

require_paused_and_clean() {
  python3 - "$SIM_BASE_URL" <<'PY'
import json, sys, urllib.request
base = sys.argv[1]
def get(path):
    with urllib.request.urlopen(base + path, timeout=5) as response:
        return json.load(response)
instance = get('/v1/instance')
faults = get('/admin/faults')
active = [fault.get('id') for fault in faults if fault.get('active')]
if instance.get('status') != 'PAUSED':
    raise SystemExit(f"simulator must be PAUSED; found {instance.get('status')}")
if active:
    raise SystemExit(f"refusing to run with pre-existing active faults: {active}")
print(f"Preflight: PAUSED at tick {instance['tick']}; no active faults")
PY
}

data_health() {
  curl --fail --silent --show-error "$API_BASE_URL/api/data-health"
}

wait_for_data_recovery() {
  local attempt payload
  for attempt in $(seq 1 40); do
    if payload=$(data_health 2>/dev/null) && python3 -c \
      'import json,sys;x=json.load(sys.stdin);sys.exit(0 if x.get("data_status")=="HEALTHY" and not x.get("stale") else 1)' \
      <<<"$payload"; then
      echo "Recovery verified: $payload"
      return 0
    fi
    sleep 1
  done
  echo "FAIL: snapshot did not recover within 40 seconds; last response: ${payload:-unavailable}" >&2
  return 1
}

wait_for_stream_recovery() {
  local since="$1" attempt logs
  for attempt in $(seq 1 40); do
    logs=$(docker compose logs --no-color --since "$since" worker 2>&1 || true)
    if grep -q '"event": "simulator_stream_connected"' <<<"$logs"; then
      grep '"event": "simulator_stream_connected"' <<<"$logs" | tail -1
      echo "SSE recovery verified after fault clear without another worker restart."
      return 0
    fi
    sleep 1
  done
  echo "FAIL: worker did not log successful SSE reconnection after clearing stream fault" >&2
  return 1
}

fault_probe() {
  local fault="$1" headers body status elapsed
  headers=$(mktemp)
  body=$(mktemp)
  case "$fault" in
    unavailable|error_rate)
      status=$(curl --silent --show-error -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/instance")
      echo "Probe $fault: HTTP $status; response $(cat "$body")"
      [[ "$status" == 503 ]]
      ;;
    latency)
      elapsed=$(curl --silent --show-error --max-time 8 -o "$body" -w '%{time_total}' "$SIM_BASE_URL/v1/instance")
      echo "Probe latency: HTTP response received in ${elapsed}s (fault injects 3500ms; client read timeout is 3s)"
      python3 -c 'import sys;sys.exit(0 if float(sys.argv[1]) >= 3.0 else 1)' "$elapsed"
      ;;
    stale_data)
      status=$(curl --silent --show-error -D "$headers" -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/instance")
      echo "Probe stale_data: HTTP $status; $(tr -d '\r' <"$headers" | grep -i '^x-simulator-stale:' || true)"
      [[ "$status" == 200 ]] && tr -d '\r' <"$headers" | grep -qi '^x-simulator-stale: true'
      ;;
    stream_disconnect)
      status=$(curl --silent --show-error --max-time 5 -N -D "$headers" -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/stream" || true)
      echo "Probe stream_disconnect: HTTP $status; response $(head -c 200 "$body")"
      [[ "$status" == 503 ]]
      ;;
  esac
  rm -f "$headers" "$body"
}

scene() {
  local fault="$1" params="$2" fault_start=""
  echo "Scene: $fault — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write."
  if [[ "$fault" == stream_disconnect ]]; then
    docker compose stop worker >/dev/null
    worker_stopped=1
  fi
  fault_start=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  fault_active=1
  curl --fail --silent --show-error -H 'Content-Type: application/json' \
    -d "{\"type\":\"$fault\",\"duration_seconds\":$FAULT_SECONDS,\"parameters\":$params}" \
    "$SIM_BASE_URL/admin/faults"
  echo
  if [[ "$fault" == stream_disconnect ]]; then
    docker compose start worker >/dev/null
    worker_stopped=0
  fi
  fault_probe "$fault"
  sleep "$WAIT_SECONDS"
  echo "During $fault data-health: $(data_health)"
  echo "During $fault worker signals:"
  curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | grep -E '^(sim_client_retries_total|sim_client_failures_total|sim_breaker_state|snapshot_rejected_total|worker_sse_reconnects_total)' || true
  clear_fault
  echo "Cleared $fault; waiting for an accepted non-stale REST snapshot."
  wait_for_data_recovery
  if [[ "$fault" == stream_disconnect ]]; then
    wait_for_stream_recovery "$fault_start"
  fi
}

require_paused_and_clean

for fault in unavailable error_rate latency stale_data stream_disconnect; do
  case "$fault" in
    error_rate) params='{"rate":1.0}' ;;
    latency) params='{"delay_ms":3500}' ;;
    *) params='{}' ;;
  esac
  scene "$fault" "$params"
done

echo 'Scene: malformed simulator data — test-only malformed response; simulator state is unchanged.'
"$PYTHON_BIN" -m pytest -q tests/integration/test_resilience.py -k malformed_data_fault

echo 'Scene: predictor unavailable — expected baseline fallback, low confidence, incident and fallback metric.'
before=$(curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | awk '/^policy_fallback_total/ {sum += $NF} END {print sum+0}')
docker compose stop predictor >/dev/null
predictor_stopped=1
curl --silent --show-error "$API_BASE_URL/api/health"
echo
curl --fail --silent --show-error -H 'Content-Type: application/json' -X POST \
  "$SIM_BASE_URL/admin/step" >/dev/null
echo "Stepped simulator once to produce a new forecast input while predictor was stopped."
sleep 8
after=$(curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | awk '/^policy_fallback_total/ {sum += $NF} END {print sum+0}')
echo "Predictor fallback counter before=$before after=$after"
python3 -c 'import sys;sys.exit(0 if float(sys.argv[2]) > float(sys.argv[1]) else 1)' "$before" "$after"
curl --fail --silent --show-error "$API_BASE_URL/api/risks" | python3 -c '
import json,sys
payload=json.load(sys.stdin); forecasts=payload["forecasts"]
latest=max((item["tick"] for item in forecasts), default=-1)
rows=[item for item in forecasts if item["tick"]==latest]
if not rows or any(item["source"]!="baseline" or not item["needs_review"] or item["confidence"]>0.4 for item in rows):
    raise SystemExit("FAIL: predictor outage did not persist review-required baseline forecasts")
maximum=max(item["confidence"] for item in rows)
print(f"Fallback verified: tick={latest}; forecasts={len(rows)}; source=baseline; all require review; max confidence={maximum:.3f}")
'
curl --fail --silent --show-error "$API_BASE_URL/api/events" | python3 -c '
import json,sys
payload=json.load(sys.stdin)
if not any(item.get("type")=="predictor_fallback" and item.get("resolved_at") is None for item in payload.get("incidents", [])):
    raise SystemExit("FAIL: active predictor fallback incident was not persisted")
print("Predictor fallback incident verified in API.")
'
docker compose start predictor >/dev/null
predictor_stopped=0
sleep 11
curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/step" >/dev/null
echo "Stepped simulator once after predictor recovery to produce a remote forecast input."
sleep 8
curl --fail --silent --show-error "$API_BASE_URL/api/health"
echo
curl --fail --silent --show-error "$API_BASE_URL/api/risks" | python3 -c '
import json,sys
payload=json.load(sys.stdin); forecasts=payload["forecasts"]
latest=max((item["tick"] for item in forecasts), default=-1)
rows=[item for item in forecasts if item["tick"]==latest]
if not rows or any(item["source"]!="remote" for item in rows):
    raise SystemExit("FAIL: predictor recovery did not replace persisted fallback forecasts with remote forecasts")
print(f"Recovery verified: tick={latest}; forecasts={len(rows)}; source=remote")
'

echo 'Scene: worker unavailable — API and frontend remain reachable while snapshot age advances.'
docker compose stop worker >/dev/null
worker_stopped=1
sleep 18
curl --fail --silent --show-error "$API_BASE_URL/api/health"
echo
curl --fail --silent --show-error "$API_BASE_URL/api/data-health"
echo
curl --fail --silent --show-error "$FRONTEND_BASE_URL/" >/dev/null
echo 'Frontend HTTP 200 while worker is stopped.'
docker compose start worker >/dev/null
worker_stopped=0
wait_for_data_recovery

clear_fault
python3 - "$SIM_BASE_URL" <<'PY'
import json, sys, urllib.request
base = sys.argv[1]
with urllib.request.urlopen(base + '/admin/faults', timeout=5) as response:
    active = [fault for fault in json.load(response) if fault.get('active')]
with urllib.request.urlopen(base + '/admin/events', timeout=5) as response:
    events = json.load(response)
with urllib.request.urlopen(base + '/v1/instance', timeout=5) as response:
    instance = json.load(response)
if active:
    raise SystemExit(f"active faults remain: {active}")
if any(event.get('status') == 'ACTIVE' for event in events):
    raise SystemExit('unresolved simulator events remain')
if instance.get('status') != 'PAUSED':
    raise SystemExit(f"simulator not paused: {instance.get('status')}")
print(f"Final state: PAUSED tick {instance['tick']}; faults clear; events resolved")
PY
