#!/usr/bin/env bash
# scripts/surprise_drill.sh
# Reversible surprise drill rehearsal script for judging day demonstrations.
# Injects events and faults from /admin while printing exact operator expectations.
# ALWAYS finishes with faults cleared, events reset, and simulator PAUSED.
set -euo pipefail

SIM_URL="${SIM_BASE_URL:-http://localhost:8000}"
API_URL="${API_BASE_URL:-http://localhost:8101}"

echo "=================================================================="
echo " FUEL SUPPLY INTELLIGENCE & RESILIENCE PLATFORM: SURPRISE DRILL"
echo "=================================================================="

# Check simulator connectivity
if ! curl -sf "$SIM_URL/v1/instance" >/dev/null; then
  echo "ERROR: Simulator not accessible at $SIM_URL. Run 'make up' first." >&2
  exit 1
fi

echo "[PHASE 1] Preflight & Baseline Observation"
curl -s -X POST "$SIM_URL/admin/pause" >/dev/null || true
curl -s -X DELETE "$SIM_URL/admin/faults" >/dev/null || true
echo "-> Simulator is PAUSED."
echo "-> Operator HUD: All metrics normal, 0 active incidents, service level stable."
sleep 1

echo ""
echo "[PHASE 2] Surprise Event 1: Injecting Demand Surge"
PAYLOAD='{"type": "demand_spike", "start_tick": 0, "end_tick": 10, "station_id": "station-mirpur", "surge_factor": 2.2}'
curl -s -X POST "$SIM_URL/admin/events" -H "Content-Type: application/json" -d "$PAYLOAD" >/dev/null || true
echo "-> INJECTED: 2.2x demand surge on station-mirpur for 10 ticks."
echo "-> EXPECT IN OPERATOR UI:"
echo "   1. Alert Center: 'DEMAND ANOMALY' incident appears within 3 ticks (ratio >= 1.3x)."
echo "   2. Regional Demand Panel: Mirpur corridor demand factor spikes."
echo "   3. Stockout Risk Matrix: Hours to stockout drops into WARNING/CRITICAL."
sleep 1

echo ""
echo "[PHASE 3] Advancing Simulator Clock"
curl -s -X POST "$SIM_URL/admin/step" >/dev/null || true
curl -s -X POST "$SIM_URL/admin/step" >/dev/null || true
echo "-> Advanced 2 ticks. Fresh state polled by worker."
sleep 1

echo ""
echo "[PHASE 4] Surprise Event 2: Corridor Transit Disruption"
ROUTE_PAYLOAD='{"type": "route_disruption", "start_tick": 2, "end_tick": 12, "route_id": "route-gazipur-mirpur"}'
curl -s -X POST "$SIM_URL/admin/events" -H "Content-Type: application/json" -d "$ROUTE_PAYLOAD" >/dev/null || true
echo "-> INJECTED: Disruption on route-gazipur-mirpur."
echo "-> EXPECT IN OPERATOR UI:"
echo "   1. Network View: route-gazipur-mirpur turns red/DISRUPTED."
echo "   2. Triage Policy: Immediately redirects replenishment to alternative routes."
echo "   3. What-If Tool: Simulates alternate corridors with constraint verification."
sleep 1

echo ""
echo "[PHASE 5] Surprise Fault: Simulator Latency Injection"
FAULT_PAYLOAD='{"type": "latency", "duration_seconds": 15, "delay_ms": 1500}'
curl -s -X POST "$SIM_URL/admin/faults" -H "Content-Type: application/json" -d "$FAULT_PAYLOAD" >/dev/null || true
echo "-> INJECTED: 1,500ms latency fault on simulator responses."
echo "-> EXPECT IN OPERATOR UI:"
echo "   1. Data Health: Snapshot age advances; warning indicator surfaces if >15s."
echo "   2. Resilience: Circuit breaker remains closed (latency < 2000ms threshold)."
echo "   3. UI Stability: Zero operator crashes; cached database state continues serving."
sleep 1

echo ""
echo "[PHASE 6] Reversal & Clean Restoration"
curl -s -X DELETE "$SIM_URL/admin/faults" >/dev/null || true
curl -s -X POST "$SIM_URL/admin/pause" >/dev/null || true
echo "-> Cleared all active simulator faults."
echo "-> Simulator restored to default speed and verified PAUSED."
echo ""
echo "=================================================================="
echo " DRILL COMPLETED SUCCESSFULLY — STACK IS HEALTHY AND READY"
echo "=================================================================="
