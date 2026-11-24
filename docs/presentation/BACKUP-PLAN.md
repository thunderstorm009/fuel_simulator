# Judging Demo Emergency Backup Plan

**Platform:** Fuel Supply Intelligence & Resilience Platform
**Event:** BUP CSE Fest 2026 Hackathon
**Target:** Disaster Contingency Protocol for Live Presentation Day
**Companion Artifacts:** [DEMO-BACKUP.md](../DEMO-BACKUP.md), [PITCH-10MIN.md](PITCH-10MIN.md), [SLIDES.md](SLIDES.md), [slides.html](slides.html)

---

## Contingency Matrix Overview

| Threat Scenario | Likelihood | Impact | Immediate Mitigation Action |
|---|:---:|:---:|---|
| **Scenario A: Simulator Crash / Port Lock** | Medium | High | Switch to Static Demo Mode via [docs/DEMO-BACKUP.md](../DEMO-BACKUP.md) or mock responses. |
| **Scenario B: WiFi / Network Outage** | High | Low | The entire stack runs 100% locally on `localhost`. Zero external cloud dependencies. |
| **Scenario C: Projector Aspect Ratio Mismatch** | Medium | Medium | Use responsive `slides.html` or full-screen PDF slides in `docs/presentation/slides.pdf`. |
| **Scenario D: Presentation Cut to 3 Minutes** | Medium | High | Execute Emergency 3-Minute Lightning Pitch (documented below). |
| **Scenario E: Port Conflicts on Host Machine** | Low | Medium | Modify `API_HOST_PORT` and `FRONTEND_HOST_PORT` in `.env` and restart. |

---

## Scenario A: Upstream Simulator Unresponsive or Crashing

If the official simulator container freezes, crashes, or fails to initialize:

1. **Check Simulator Health:**
   ```bash
   curl -s http://localhost:8000/v1/health || docker compose restart simulator
   ```
2. **Engage Degraded Mode Demonstration:**
   - Use the failure as a **live resilience demonstration**: point out that our typed Circuit Breaker immediately tripped to `OPEN`, the UI surfaced the amber **DEGRADED MODE** banner, and cached state is safely served.
3. **Switch to Static Backup Pack:**
   - Open [docs/DEMO-BACKUP.md](../DEMO-BACKUP.md).
   - This document contains frozen, pre-verified ASCII and visual data tables for all 10 demo steps, including snapshot telemetry, diurnal forecasts, and constraint validation matrices.
   - Walk through the static screens in `docs/evidence/day-7/screens/` using `open docs/evidence/day-7/screens/01-dashboard-overview.png`.

---

## Scenario B: No Internet or Venue WiFi Failure

- **Zero External Dependencies:**
  - The platform does NOT require internet connectivity.
  - PostgreSQL, FastAPI, Worker, Predictor, Prometheus, Grafana, and Vite React run inside local Docker containers on the host machine.
  - Browser UI accesses `http://localhost:5173`.
  - Machine learning models run locally via NumPy and SciPy; zero external cloud APIs or LLM endpoints are called during core decision operations.

---

## Scenario C: Projector Failure or Display Resolution Issues

If the venue projector uses low resolution (e.g. 1024x768) or fails:

1. **Use Mobile Responsive Layout:**
   - Open Chrome DevTools (`Cmd + Option + I`), toggle device toolbar (`Cmd + Shift + M`), and select **iPhone 14 Pro** (390x844).
   - Our UI is fully mobile-responsive (verified in `docs/evidence/day-7/screens/22-mobile-responsive-view.png`).
2. **Present from PDF Deck:**
   - Open `docs/presentation/slides.pdf` in standard Preview or Acrobat Reader in full-screen mode (`Cmd + Ctrl + F`).

---

## Scenario D: Presentation Time Cut from 10 Minutes to 3 Minutes

If judges enforce a strict 3-minute lightning format:

### Emergency 3-Minute Lightning Pitch Script

> **Minute 1: The Problem & Solution (0:00 - 1:00)**
> *"Downstream fuel distribution across Bangladesh faces severe supply shocks: highway blockages, sudden panic buying, and depot truck shortages. Traditional dispatching relies on delayed spreadsheets and intuition, causing avoidable stockouts.*
> *We built the **Fuel Supply Intelligence & Resilience Platform** on top of the BUP Simulator. It implements a closed 9-stage loop: Observe, Detect, Predict, Decide, Simulate, Approve, Act, Monitor, and Recover. All operations are SIMULATED, and human authority is strictly enforced—no allocation is ever submitted autonomously."*
>
> **Minute 2: Core Capabilities & Live UI (1:00 - 2:00)**
> *[Show Dashboard: http://localhost:5173]*
> *"In the UI, we observe real-time telemetry backed by SSE push streams, cutting read traffic by 95%. Our forecasting engine runs diurnal curve models with Monte Carlo risk simulation across 300 stochastic paths.*
> *When crisis strikes, our **Two-Pass Urgency Triage** prioritizes stations facing stockout within 12 hours while strictly auditing 5 physical constraints: depot stock, station tank ullage, route status, truck capacity, and dispatch limits.*
> *Before dispatch, our **What-If Sandbox** evaluates counterfactual dispatches in under 50ms without touching the database. Finally, an operator inputs their secure token to approve, generating a permanent UUID idempotency key to prevent double dispatches."*
>
> **Minute 3: Scientific Proof & Production Rigor (2:00 - 3:00)**
> *[Show Evaluation View: http://localhost:5173/evaluation]*
> *"We proved our advantage scientifically: across a **60-scenario randomized sweep** (240 live runs), our Two-Pass Triage achieved a **97.93% service level**, beating greedy naive refill by **+0.79% [0.41%, 1.27%] 95% CI**, reducing unmet demand by **35%**, and outperforming naive by **+3.69%** on holdout disasters.*
> *The system features **262 automated tests**, **0 security vulnerabilities**, **0 critical accessibility violations**, and recovers from a wiped cold start in **36 seconds**. Thank you!"*

---

## Scenario E: Host Port Conflicts

If ports `8101` (API) or `5173` (Frontend) conflict with existing host services:

```bash
# 1. Edit .env to assign alternative host ports
echo "API_HOST_PORT=8105" >> .env
echo "FRONTEND_HOST_PORT=5175" >> .env

# 2. Recreate containers with new ports
docker compose up -d api frontend

# 3. Access frontend at http://localhost:5175
```
