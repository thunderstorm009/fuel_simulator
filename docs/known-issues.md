# Known issues and resolved acceptance status

Updated 2026-11-20. Reflects verified evidence available in this repository.

## Resolved sprint acceptance items

| Area | Resolution | Verified evidence |
|---|---|---|
| Sprint 4 live approval & replay | Completed live operator approval; allocation ID 1 reached ARRIVED at tick 137; exact replay returned identical ID | `docs/evidence/sprint-04-overnight.md` |
| Docker daemon & container health | All 8 containers healthy; cold-start recovery verified in 34 seconds from scratch | `docs/evidence/sprint-07-cold-start.txt`, `docker compose ps` |
| Sprint 5 resilience matrix | Tested against all 5 simulator faults + payload corruption + worker/predictor outages; Grafana alert fired live | `docs/evidence/sprint-05-fault-demo-accepted.txt`, `docs/evidence/sprint-05-worker-alert-check.txt` |
| Scenario comparison & determinism | Declarative scenario runner evaluated 4 scenarios × 3 policies × 2 runs; 100% deterministic (delta 0.0000) | `docs/results/scenario-summary.md`, `docs/results/scenario-results.json` |
| Load testing & performance knee | k6 benchmark completed across normal, latency fault, and predictor stopped; 205k requests, 0% errors, knee at 100 VUs | `docs/loadtest.md`, `docs/results/docker-stats-*.csv` |
| Isolated clean clone verification | Clean clone build, lint, and test suite pass completely without private local-only development files | `docs/evidence/clean-clone-check.txt` |
| Reversible chaos testing | 1.0 min random fault injection completed with zero unexplained 5xx API errors and automatic system recovery | `docs/evidence/sprint-07-chaos.json` |

## Open human-only ceremony items

The following items are intentional human responsibilities to be completed by the project owner prior to live presentation:

1. **Rehearsal:** Execute the 5-minute live operator walkthrough script three times using `docs/final-demo-script.md`.
2. **Backup video recording:** Record a 3-minute screen capture walkthrough showing the operator dashboard, approval interaction, and Grafana alert dashboard as an offline fallback.
3. **Remote repository push:** Project owner reviews branch diff (`git diff origin/main...HEAD`) and pushes tags and branch to GitHub remote (`git push origin overnight-sprints-4-7 --tags`).
