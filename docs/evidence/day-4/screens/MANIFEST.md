# Day 4 Screenshot Manifest

**Captured:** 2026-11-23T15:47:00+06:00  
**Stack Environment:** Headless Chromium against full Docker Compose stack (ports 5173, 8101, 8000)  
**Viewport:** 1440 × 960 (Device Scale Factor: 2x)  
**Simulator State at Capture:** PAUSED, tick 0, faults cleared  

---

## Screenshot Inventory

| # | Filename | Primary Route | Viewport | SHA256 Checksum | What It Proves |
|---|---|---|---|---|---|
| 01 | `01-dashboard.png` | `/` (Overview) | 1440×960 @ 2x | `73b3113ae3d1b4f7eb9b119f984ce4dafbb2b8964b3a6b8fcfeedecb1233363f` | Proves Overview HUD with prominent SIMULATED banner, stream status badge, speed, tick counter, network summary cards, and version footer (`Model v1.2.0`, `Policy v2.1.0`). |
| 02 | `02-shortage-risk.png` | `/` (`Stockout risk`) | 1440×960 @ 2x | `875e4e02b603bd81862bd7211e1ed6251e32396fe8f84a77cd181b752c1034c7` | Proves interactive shortage risk matrix with station cells, fuel type breakdowns (DIESEL, OCTANE, PETROL), hours to stockout, and probability confidence bands. |
| 03 | `03-trajectory-drawer.png` | `/` (`Stockout risk` + drawer) | 1440×960 @ 2x | `dd16ba5d601bbb5688aaba185986744b0807e907b03b8fda77f1e7a8d12c466d` | Proves interactive sliding trajectory drawer rendering p10/p50/p90 inventory forecast confidence bands, burn rates, and primary risk driver explanations. |
| 04 | `04-recommendations.png` | `/` (`Recommendations`) | 1440×960 @ 2x | `4569a7fc3d01c1e6a6a8759c6177e3762876ba7a0983f1971f7f3105586c84c1` | Proves human-in-the-loop decision workflow: recommendation cards with constraint satisfaction checklists, operator token input, operator name input, and explicit Approve/Reject buttons (no auto-submission). |
| 05 | `05-what-if.png` | `/` (`Recommendations` + What-If) | 1440×960 @ 2x | `4569a7fc3d01c1e6a6a8759c6177e3762876ba7a0983f1971f7f3105586c84c1` | Proves What-If counterfactual simulator allowing operators to model alternative depot-route-station dispatches, verifying feasibility and delta runway before committing. |
| 06 | `06-network.png` | `/` (`Network view`) | 1440×960 @ 2x | `aaeed7a153ad503c8b1b315f0dca87f92d36086c5f91bd2e13a781910773fa72` | Proves multi-depot physical corridor visualization: 4 transit routes, depot dispatch limits, station tank capacities, and real-time corridor disruption status. |
| 07 | `07-incoming-supply.png` | `/` (`Incoming supply`) | 1440×960 @ 2x | `6dc36588e77f69599c6bb82df125876ba535bff97a446c8aad5636c38a8f0b95` | Proves scheduled bulk supply arrival timeline across Gazipur and Patiya depots, distinguishing scheduled bulk shipments from retail served demand. |
| 08 | `08-alerts.png` | `/` (`Alert center`) | 1440×960 @ 2x | `d818a0840bfdd008c3baf7a8edaffc1eec69b949b87c89175d78c77c02a04508` | Proves centralized incident feed with severity tags, category filters, and operational CSV/JSON export buttons. |
| 09 | `09-system-health.png` | `/` (`System health`) | 1440×960 @ 2x | `40d277d64edd90cb343a657a2cbeca50efc0dd8f6924cd386ed8721763516534` | Proves platform observability dashboard displaying component health grid (API, Worker, Database, Simulator, Predictor), latency telemetry, and snapshot data freshness age. |
| 10 | `10-guided-tour.png` | `/` (Guided tour modal) | 1440×960 @ 2x | `54bdd9a964be010871f48bef4adbfb66b3b426a38c93ba5dba2fc19a2e8f7ae6` | Proves interactive judging walkthrough modal presenting 5-stage architectural flow (Observe, Detect, Decide, Simulate, Recover) with dismiss and reset controls. |

---

## Backward-Compatibility Aliases

To maintain 100% link integrity across existing project documentation and rehearsal slides:
- `02-guided-tour.png` -> identical to `10-guided-tour.png` (`54bdd9a9...`)
- `03-forecast-risk.png` -> identical to `02-shortage-risk.png` (`875e4e02...`)
- `06-decision-history.png` -> dedicated capture of scrolled decision history table (`98698546...`)
- `07-alerts.png` -> identical to `08-alerts.png` (`d818a084...`)
- `08-network.png` -> identical to `06-network.png` (`aaeed7a1...`)
- `09-evaluation.png` -> dedicated capture of evaluation view (`1e45153a...`)
- `10-system-health.png` -> identical to `09-system-health.png` (`40d277d6...`)
