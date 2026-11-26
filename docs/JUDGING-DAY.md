# Judging Day Runbook & Demonstration Guide

This runbook provides the exact execution commands, 10-minute presentation choreography, automated preflight check, surprise fault drill procedures, and contingency protocols for presenting the **Fuel Supply Intelligence & Resilience Platform** to the BUP CSE FEST 2026 hackathon judging panel.

---

## 1. Quick Start from a Clean Clone

To spin up the entire platform on judging day from scratch:

```bash
# 1. Clone the repository
git clone <repository-url> fuel_simulator
cd fuel_simulator

# 2. Configure environment from template
cp .env.example .env
# Ensure OPERATOR_TOKEN=secret-judge-token in .env

# 3. Bring up full stack (8 containers)
make up

# 4. Verify preflight readiness (automated check of Docker, ports, keys, simulator state, disk)
make preflight
```

All 8 containers (`simulator`, `postgres`, `api`, `worker`, `predictor`, `frontend`, `prometheus`, `grafana`) will report **HEALTHY** within ~36 seconds (with pre-built images). `make preflight` verifies complete readiness and exits with `>>> PREFLIGHT VERDICT: GO <<<`.

### URLs to have open in browser tabs:
1. **Operator Web App:** `http://localhost:5173` (or `http://localhost:5174`)
2. **Grafana Dashboards:** `http://localhost:3000/d/fuel-supply-platform` (Login: `admin` / `local-demo-only`)
3. **Prometheus Targets:** `http://localhost:9090/targets` (All 3 targets UP)
4. **Interactive API Docs:** `http://localhost:8101/docs`

---

## 2. Interactive Demo Director & Rehearsals

For judging presentations, the repository includes an automated **Demo Director** script that guides the presenter step-by-step through the 10-minute demonstration, controls simulation ticks, and provides live talking points:

```bash
# Run interactive live demonstration director
make demo
# Or directly via script with speed control:
python3 scripts/demo_director.py --speed 1.0
```

### Pre-judging Dry Run:
To verify the full storyline in advance without modifying simulator state:
```bash
python3 scripts/demo_director.py --dry-run
```

Three consecutive automated dry-run rehearsals were executed and logged with step timings in `docs/evidence/day-4/demo-rehearsal-*.json` (and Day 7 dry runs in `docs/evidence/day-7/rehearsal.md`):
- **Rehearsal 1:** 8.1s execution time, 6/6 steps completed cleanly.
- **Rehearsal 2:** 8.0s execution time, 6/6 steps completed cleanly.
- **Rehearsal 3:** 8.1s execution time, 6/6 steps completed cleanly.

To reset simulator state back to standard PAUSED baseline at any time:
```bash
make demo-reset
```

---

## 3. The 10-Minute Demonstration Script

| Time | Stage | Action & Key Talking Points |
|---|---|---|
| **0:00 - 1:30** | **Operational HUD & High-Level Architecture** | - Open `http://localhost:5173`. Point out prominent **SIMULATED** status badges, data freshness timer, active policy indicator (`two_pass_urgency_12h_then_target`), and **LIVE PUSH** SSE status.<br>- Explain the core 9-stage operational loop: *Observe, Detect, Predict, Decide, Simulate, Approve, Act, Monitor, Recover*.<br>- Highlight architectural rule 2: API never queries the simulator on read paths; all reads are served from PostgreSQL cache in sub-millisecond time.<br>- Optional: launch the accessible **Interactive Guided Tour** (`✦ Interactive Judging Tour`) to demonstrate operator onboarding. |
| **1:30 - 3:30** | **Predictive Intelligence & Trajectory Drawer** | - Navigate to **Stockout Risk** tab.<br>- Click on a station/fuel card (e.g., `station-coxsbazar` / `DIESEL`) to open the **Trajectory Drawer**.<br>- Show the 24-hour projected inventory trajectory with empirical diurnal cycle, P10/P90 Monte Carlo confidence bounds, and hours-to-stockout calculation.<br>- Reference committed backtesting results (`docs/results/backtest-summary.md`): 2.10% 24h outside-event MAPE (2.71% overall 24h) across 3,152 ticks, Brier calibration score **0.1558** with 0-tick spike convergence in Event-Aware v1.2.0 model. |
| **3:30 - 5:30** | **Constrained Triage & What-If Simulation** | - Navigate to **Recommendations** tab.<br>- Inspect an urgency-ranked allocation card showing the two-pass triage heuristic.<br>- Show the **Constraint Verification Checklist** (all 5 hard physical rules checked in pure Python with zero side-effects).<br>- Highlight measured failure boundaries (`docs/results/failure-boundary.md`): heuristic sustains 99% SLA up to 2.43x demand surge vs naive at 1.96x; binding constraint is route truck shipment cap (5-7k L), not depot dispatch capacity (23k L/tick).<br>- Click **Simulate Candidate (What-If)**: Adjust quantity slider. Watch projected hours-to-stockout and depot net cover update in real-time (14.67 ms p50 / 18.87 ms p95 unloaded; 514.49 ms p95 under 100 VU combined load).<br>- Demonstrate the **Human Approval Gate**: Enter operator token and operator name into the memory-only token field and click **Approve**. Explain that the worker will re-read fresh non-stale state and re-validate all 5 constraints immediately before the simulator write. |
| **5:30 - 7:00** | **Decision History, Auditing & Export** | - Navigate to **Decisions** tab.<br>- Show the audit trail logging actor name, action (`APPROVED` / `REJECTED`), timestamp, and permanent UUID idempotency key.<br>- Demonstrate filtering and sorting by actor and status.<br>- Click **Export CSV** and **Export JSON** to show regulatory compliance and audit export readiness. |
| **7:00 - 8:30** | **Surprise Crisis Injects & Anomaly Detection** | - Run `bash scripts/surprise_drill.sh` in terminal (or director step 3 & 4).<br>- Show **Alert Center**: Point out automated detection incidents (`demand_anomaly`, `route_disruption`).<br>- Click **Explain Incident** on an anomaly: Show the plain-language explanation generated deterministically by `TemplateSummarizer`, marked with the disclaimer: `AI-generated summary of simulated data`.<br>- Show **Network View**: Point out the disrupted route rendered in red (`DISRUPTED`) and trucks in transit. |
| **8:30 - 10:00** | **Resilience, SSE Push & Measured Recovery** | - Open Grafana `http://localhost:3000/d/fuel-supply-platform`.<br>- Show 4 observability layers: application rates (615.3 req/s @ 100 VUs, 625.8 req/s @ 200 VUs in Sprint 12 sweep), system memory/CPU, intelligence metrics, and circuit breaker status.<br>- Point out that under upstream simulator latency faults or complete predictor outages, the platform gracefully switches to baseline heuristic fallback with zero 5xx errors (0.0% error rate across k6 runs).<br>- Show measured database recovery: **2.93s `psql` restore RTO** restoring full schema and data with zero duplicate submissions.<br>- Conclude with the cold-start benchmark: 36 seconds recovery from completely wiped storage (with pre-built images). |

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
4. Injects a 1,500ms latency fault; verifies cached reads stay responsive and circuit breaker trips gracefully.
5. **Reverses all faults, clears events, and leaves the simulator PAUSED.**

---

## 5. Contingency Protocols (Troubleshooting Under Pressure)

| Issue | Root Cause | Immediate Fix |
|---|---|---|
| **Port Clash** (e.g. 5432, 8000, 3000, 5173 in use) | Another daemon or PostgreSQL running on host | Run `lsof -i :<port>` and kill host process, or set `FRONTEND_HOST_PORT=5174` in `.env` and restart frontend. |
| **Simulator not PAUSED** | Clock left running from previous test | Run `curl -X POST http://localhost:8000/admin/pause` or `make demo-reset`. |
| **Container crash or Docker timeout** | Host memory exhaustion | Run `bash scripts/rollback.sh` to trigger automated health verification and recovery. |
| **Database state corrupted or dirty** | Previous destructive testing | Run `python3 scripts/drill_backup_restore.py` to restore in 2.93s, or `docker compose down -v && make up` (takes ~34s to restore clean schema). |
| **Token rejected during approval** | Missing or mismatched `OPERATOR_TOKEN` | Confirm token matches `.env`. UI token field stores value purely in browser memory. |
| **Hardware or Network Catastrophic Failure** | Host display or Docker failure | Open **`docs/DEMO-BACKUP.md`**: ordered screenshot slides with exact voiceover narrative script. |

---

## 6. Verification Checklist Before Calling Judges

- [x] Preflight checks pass: `make preflight` exits 0 with `GO`.
- [x] All 8 containers healthy (`make smoke` exits 0).
- [x] Simulator is **PAUSED** at default speed (`curl -s http://localhost:8000/v1/instance` reports `"status":"PAUSED"`).
- [x] Active simulator faults are **CLEARED** (`curl -s http://localhost:8000/admin/faults` returns 0 active faults).
- [x] Mechanical gates pass cleanly: `bash scripts/sprint_gate_public.sh 16`.
- [x] Three automated dry-run rehearsals executed (`docs/evidence/day-7/rehearsal.md`); 3 human live rehearsals pending presenter practice.
- [x] Playwright E2E browser test suite passes (`make test-e2e`: 12 passed).
- [x] Browser tabs open: Operator Dashboard (`:5173`), Grafana (`:3000`), Prometheus (`:9090`), API docs (`:8101/docs`).
- [x] Offline fallback pack ready: `docs/DEMO-BACKUP.md`.
