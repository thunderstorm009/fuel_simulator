# Judging Day Runbook & Demonstration Guide

This runbook provides the exact execution commands, 10-minute presentation choreography, surprise fault drill procedures, and contingency protocols for presenting the **Fuel Supply Intelligence & Resilience Platform** to the BUP CSE FEST 2026 hackathon judging panel.

---

## 1. Quick Start from a Clean Clone

To spin up the entire platform on judging day from scratch:

```bash
# 1. Clone the repository
git clone <repository-url> fuel_simulator
cd fuel_simulator

# 2. Configure environment from template
cp .env.example .env
# Set OPERATOR_TOKEN=secret-judge-token in .env

# 3. Bring up full stack (8 containers)
make up

# 4. Verify system health
make smoke
```

All 8 containers (`simulator`, `postgres`, `api`, `worker`, `predictor`, `frontend`, `prometheus`, `grafana`) will report **HEALTHY** within 35 seconds.

### URLs to have open in browser tabs:
1. **Operator Web App:** `http://localhost:5173` (or `http://localhost:5174`)
2. **Grafana Dashboards:** `http://localhost:3000` (Login: `admin` / `local-demo-only`)
3. **Prometheus Targets:** `http://localhost:9090/targets` (All 3 targets UP)
4. **Interactive API Docs:** `http://localhost:8101/docs`

---

## 2. Simulation Speed & Demo Clock Settings

The platform includes two ways to advance simulation time for judges:

### Recommended: Controllable Demo Clock
Run the controlled demo clock in a separate terminal:
```bash
./scripts/demo_clock.py --rate 0.5
```
This advances the simulator at **0.5 ticks/second** (1 tick every 2 seconds, representing 15 simulated minutes), providing the ideal pace for human operator review without triggering speed expiration warnings.

### Alternative: Continuous Running Mode
If the judge requests running the simulator at full continuous speed:
```bash
curl -X POST http://localhost:8000/admin/run
```
The operator UI will immediately display the dynamic speed warning banner (`High simulation speed detected (>0.5 ticks/sec)`), demonstrating the platform's adaptive telemetry and pre-submission staleness guards.

---

## 3. The 10-Minute Demonstration Script

| Time | Stage | Action & Key Talking Points |
|---|---|---|
| **0:00 - 2:00** | **Architecture & HUD Overview** | - Open `http://localhost:5173`. Point out **SIMULATED** status badges, data freshness timer, and system health status.<br>- Explain the core operational loop: *Observe, Detect, Predict, Decide, Simulate, Approve, Act, Monitor, Recover*.<br>- Highlight that all domain reads come from local PostgreSQL cache; the API never queries the simulator on read paths (AGENTS.md rule 2). |
| **2:00 - 4:00** | **Predictive Intelligence & Trajectory** | - Navigate to **Stockout Risk** tab.<br>- Click on a station/fuel card (e.g., `station-coxsbazar` / `DIESEL`) to open the **Trajectory Drawer**.<br>- Show the 24-hour projected inventory trajectory with empirical diurnal cycle, P10/P90 Monte Carlo confidence bounds, and hours-to-stockout calculation.<br>- Reference committed backtesting results (`docs/results/backtest-summary.md`: 2.11% MAPE over 24h across 2,000 historical ticks). |
| **4:00 - 6:00** | **Constrained Triage & What-If Simulation** | - Navigate to **Allocations** tab.<br>- Inspect an urgency-ranked allocation card showing the two-pass triage heuristic (`two_pass_urgency_12h_then_target`).<br>- Show the **Constraint Verification Checklist** (all 5 hard physical rules checked in pure code).<br>- Click **Simulate Candidate (What-If)**: Adjust quantity slider from 5,000 to 12,000 L. Watch projected hours-to-stockout and depot net cover update in real-time (<50ms unloaded, zero database writes; ~834ms under 100 VU load).<br>- Demonstrate the **Human Approval Gate**: Enter operator token into the memory-only token field and click **Approve**. Explain that the worker will re-read fresh non-stale state and re-validate all 5 constraints immediately before the simulator write. |
| **6:00 - 8:00** | **Surprise Crisis Injects & Anomaly Detection** | - Run `bash scripts/surprise_drill.sh` in terminal.<br>- Show **Alert Center**: Point out automated detection incidents (`demand_anomaly`, `route_disruption`).<br>- Click **Explain Incident** on an anomaly: Show the plain-language explanation generated deterministically by `TemplateSummarizer` (or bounded LLM), marked with the disclaimer: `AI-generated summary of simulated data`.<br>- Show **Network View**: Point out the disrupted route rendered in red (`DISRUPTED`) and trucks in transit. |
| **8:00 - 10:00** | **Resilience, Circuit Breaker & Recovery** | - Open Grafana `http://localhost:3000/d/fuel-supply-platform`.<br>- Show 4 observability layers: application rates, system memory/CPU, intelligence metrics, and circuit breaker status.<br>- Point out that under upstream simulator latency faults or complete predictor outages, the platform gracefully switches to baseline heuristic fallback with zero 5xx errors (0.0% error rate across 205k requests).<br>- Conclude with the cold-start benchmark: 34 seconds recovery from completely wiped storage. |

---

## 4. Rehearsing Surprise Injects (`scripts/surprise_drill.sh`)

Judges frequently inject unannounced events or faults during presentations. To rehearse this scenario:

```bash
bash scripts/surprise_drill.sh
```

What the script does:
1. Injects a 2.2x demand surge on `station-mirpur`.
2. Advances clock 2 ticks; verifies `demand_anomaly` alert fires in Alert Center.
3. Injects a corridor disruption on `route-gazipur-mirpur`; verifies Network View status changes.
4. Injects a 1,500ms latency fault; verifies cached reads stay responsive.
5. **Reverses all faults, clears events, and leaves the simulator PAUSED.**

---

## 5. Contingency Protocols (Troubleshooting Under Pressure)

| Issue | Root Cause | Immediate Fix |
|---|---|---|
| **Port Clash** (e.g. 5432, 8000, 3000 in use) | Another daemon or PostgreSQL running on host | Run `lsof -i :<port>` and kill host process, or override port in `.env` (e.g. `FRONTEND_HOST_PORT=5174`). |
| **Simulator not PAUSED** | Clock left running from previous test | Run `curl -X POST http://localhost:8000/admin/pause`. |
| **Container crash or Docker timeout** | Host memory exhaustion | Run `bash scripts/rollback.sh` to trigger automated health verification and recovery. |
| **Database state corrupted or dirty** | Previous destructive testing | Run `docker compose down -v && make up` (takes ~34 seconds to restore clean schema). |
| **Token rejected during approval** | Missing or mismatched `OPERATOR_TOKEN` | Confirm token matches `.env`. UI token field stores value purely in browser memory. |

---

## 6. Verification Checklist Before Calling Judges

- [x] All 8 containers healthy (`make smoke` exits 0).
- [x] Simulator is **PAUSED** at default speed (`curl -s http://localhost:8000/v1/instance` reports `"status":"PAUSED"`).
- [x] Active simulator faults are **CLEARED** (`curl -s http://localhost:8000/admin/faults` returns `[]`).
- [x] Mechanical gate passes cleanly: `bash scripts/sprint_gate.sh 10`.
- [x] Browser tabs open: Operator Dashboard, Grafana, Prometheus, API docs.
