# Known issues and resolved acceptance status

Updated 2026-11-26 (Final Independent Audit, `v1.0.1`). Reflects verified evidence available in this repository.

## Resolved sprint acceptance items

| Area | Resolution | Verified evidence |
|---|---|---|
| Sprint 4 live approval & replay | Completed live operator approval; exact replay returned identical allocation ID | `docs/evidence/sprint-04-overnight.md` |
| Docker daemon & container health | All 8 containers healthy; cold-start from wiped volumes verified in 36s (pre-built images) | `docs/evidence/day-6/cold-start.txt`, `make smoke` |
| Sprint 5 & 14 resilience matrix | Tested against all 5 simulator faults + payload corruption + worker/predictor outages | `docs/DAY-6-UPDATE.md`, `docs/results/recovery-times.json` |
| Scenario comparison & determinism | Declarative scenario runner (54 runs) + 60-scenario sweep (240 runs, `seed=42`, `+0.79% [0.41%, 1.27%]`, 1 loss `holdout_08`) | `docs/results/scenario-summary.md`, `docs/results/scenario-sweep.md` |
| Load testing & performance | Clean-clone `loadtest/k6.js` (100 VUs): `374.57 req/s`, read p95 `378.84 ms`, What-If p95 `514.49 ms`, 0% errors; Sprint 12 sweep: `615.3 req/s` @ 100 VUs (`338.3 ms` p95), `625.8 req/s` @ 200 VUs (`622.5 ms` p95) | `docs/evidence/final/verification.md`, `docs/results/k6-optimized-sweep.json` |
| Isolated clean clone verification | Clean clone build, lint, and all 264 tests pass without private local-only files | `docs/evidence/final/verification.md`, `scripts/verify_clean_clone.sh` |
| Accessibility (automated axe-core) | Fixed `color-contrast` and `label-content-name-mismatch` (ADR-054); 0 Critical, 0 Serious across all 8 views | `docs/evidence/final/browser-audit.md` |
| Localhost port binding | Bound Prometheus (9090), Grafana (3000), and Alertmanager (9093) to `127.0.0.1` (ADR-053) | `docker-compose.yml`, `tests/integration/test_compose_config.py` |

## Known limitations

1. **Latency under high concurrency:** Combined read + What-If `loadtest/k6.js` crosses the 300 ms p95 threshold at 100+ VUs (`378.84 ms` on clean-clone run; `338.3 ms` in Sprint 12 sweep) with 0% HTTP errors.
2. **24h forecast interval coverage:** In `docs/results/backtest-summary.md`, 24h P10–P90 coverage is `31.31%` (under-coverage at longer horizons vs `94.49%` at 1h).
3. **Optional items:** Reinforcement learning, Kubernetes/Helm/Terraform/GitOps, blue/green/canary/autoscaling, distributed tracing, multi-agent systems, and Kafka are intentionally `OPTIONAL-SKIPPED` (`docs/BRIEF-COMPLIANCE.md`).

## Open human-only ceremony items

1. **Three live human rehearsals:** Presenter must practice the 10-minute walkthrough three times using `docs/presentation/PITCH-10MIN.md` and `docs/presentation/NUMBERS-TO-SAY.md`.
2. **Backup video recording:** Record a 3-minute screen capture walkthrough as an offline fallback (`docs/presentation/BACKUP-PLAN.md`).
3. **Repository decisions:** Choose a `LICENSE`, decide whether to keep `reference/` public, and optionally publish a GitHub Release.
