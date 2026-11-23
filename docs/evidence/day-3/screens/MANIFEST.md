# Day 3 Screenshot Manifest

- **Date:** 2026-11-21
- **Target Resolution:** Desktop 1440 × 960 (2x Retina device scale factor, 2880 × 1920 effective)
- **Capture Engine:** Headless Google Chrome via Puppeteer (invoked from `/tmp/screenshot-tool/`)
- **Application Environment:** Docker Compose production topology (`http://localhost:5173`, `http://localhost:3000`, `http://localhost:9090`)

| File | Route / Component | Simulator Tick | Capture Time (UTC) | Viewport | What It Proves |
|---|---|---|---|---|---|
| `01-dashboard.png` | `http://localhost:5173/` (`overview`) | Tick 58 | 2026-11-21T08:49:15Z | 1440 × 960 @ 2x | High-level operational command overview showing service level, unmet demand, simulated banner, and live telemetry during regional demand spike. |
| `02-inventory.png` | `overview` (scrolled) | Tick 58 | 2026-11-21T08:49:18Z | 1440 × 960 @ 2x | Station inventory matrix across DIESEL, PETROL, OCTANE showing tank capacities, stock bars, and depot bulk reserve levels. |
| `03-forecast-risk.png` | `risk` (`RiskMatrix` + `TrajectoryDrawer`) | Tick 58 | 2026-11-21T08:49:22Z | 1440 × 960 @ 2x | Multi-station shortage risk ranking with open Recharts trajectory drawer showing 24-hour stock projection and confidence bounds. |
| `04-recommendations.png` | `recommendations` (`RecommendationsPage`) | Tick 58 | 2026-11-21T08:49:26Z | 1440 × 960 @ 2x | Constrained recommendation cards with expanded physical constraint checklist, supply drivers, and human approval controls. |
| `05-what-if.png` | `recommendations` (`WhatIfSimulator`) | Tick 58 | 2026-11-21T08:49:29Z | 1440 × 960 @ 2x | Interactive What-If simulation sandbox showing before/after inventory and stockout averted calculation (<50ms unloaded, ~834ms under 100 VU load) prior to approval. |
| `06-alerts.png` | `alerts` (`AlertCenterPage`) | Tick 58 | 2026-11-21T08:49:33Z | 1440 × 960 @ 2x | Real-time crisis alert center showing detected demand anomaly incidents with severity badges and generative plain-text briefing modal. |
| `07-regional-demand.png` | `overview` (`RegionalDemandPanel`) | Tick 58 | 2026-11-21T08:49:20Z | 1440 × 960 @ 2x | Aggregated regional fuel demand breakdown across Dhaka and Chattogram regions across highway, urban, industrial, and regional profiles. |
| `08-incoming-supply.png` | `supply` (`IncomingSupplyView`) | Tick 58 | 2026-11-21T08:49:36Z | 1440 × 960 @ 2x | Scheduled depot deliveries pipeline showing arrival ticks, quantities, and in-transit truck movements. |
| `09-network.png` | `network` (`NetworkView`) | Tick 58 | 2026-11-21T08:49:39Z | 1440 × 960 @ 2x | Supply network topology visual graph mapping regional depots, road corridors, retail stations, and active routes. |
| `10-evaluation.png` | `evaluation` (`EvaluationPage`) | Tick 58 | 2026-11-21T08:49:43Z | 1440 × 960 @ 2x | Empirical backtest accuracy curves across 1h–24h horizons (2.1%–3.1% MAPE) and scenario policy performance comparison. |
| `11-decision-history.png` | `recommendations` (`DecisionHistoryTable`) | Tick 58 | 2026-11-21T08:49:31Z | 1440 × 960 @ 2x | Permanent audit log proving owner-authorized human approval and worker submission reaching ARRIVED status in simulator. |
| `12-health-healthy.png` | `health` (`SystemHealthTab`) | Tick 58 | 2026-11-21T08:49:46Z | 1440 × 960 @ 2x | Multi-service health monitoring displaying Backend API, Worker, Predictor, Database, and Simulator status with data freshness age. |
| `13-footer-version.png` | Global (`Footer`) | Tick 58 | 2026-11-21T08:49:48Z | 1440 × 960 @ 2x | Application provenance footer displaying Git commit SHA, release tag, Model Version (1.1.0), Policy Version (2.1.0), and SIMULATED badge. |
| `14-health-degraded.png` | `health` (`SystemHealthTab`) | Tick 60 | 2026-11-21T08:49:55Z | 1440 × 960 @ 2x | Live graceful degradation during injected simulator outage; displays prominent warning banner and stale data advisory. |
| `15-grafana-fault.png` | `http://localhost:3000/d/fuel-supply-platform/` | Tick 60 | 2026-11-21T08:50:04Z | 1440 × 960 @ 2x | Provisioned 4-layer Grafana dashboard showing latency spike and error rates during injected simulator fault. |
| `16-grafana-normal.png` | `http://localhost:3000/d/fuel-supply-platform/` | Tick 67 | 2026-11-21T08:50:14Z | 1440 × 960 @ 2x | Provisioned Grafana dashboard showing automatic recovery to healthy baseline after clearing fault. |
| `17-prometheus-alerts.png` | `http://localhost:9090/alerts` | Tick 67 | 2026-11-21T08:50:18Z | 1440 × 960 @ 2x | Prometheus alerting console verifying 5 active alerting rules as code (circuit breakers, stale data, stockout risk, fallback, drift). |
