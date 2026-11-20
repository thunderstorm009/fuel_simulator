# Known issues and open acceptance gaps

Updated 2026-11-20. This list reflects evidence available in this worktree.

| Issue | Impact | Status / evidence |
|---|---|---|
| Sprint 4 live approval, `ARRIVED`, and exact-key replay not verified | Live simulator write acceptance remains open | No approved recommendation is recorded. Approval requires an explicit operator decision. |
| Docker daemon unavailable in current environment | Compose, simulator, Grafana, predictor-stop, worker-stop, and cold-start checks cannot run | `docker compose ps` failed to connect to `/Users/abrar/.docker/run/docker.sock`; current local endpoints refused connections. |
| Sprint 5 live fault/recovery matrix not rerun | New runtime behavior is covered locally but not demonstrated end to end | Prior Sprint 2 live evidence is historical; current `scripts/fault_demo.sh` was not run. |
| Scenario comparison runner absent | No heuristic-vs-naive-vs-do-nothing service-level result | Sprint 6 scenario flow's auto-approval conflicts with the explicit human approval requirement unless run in an isolated simulator with separate authorization. |
| Load tests not measured | No p95/p99, throughput, error-rate, or knee claim | k6 workload and report tooling are present; k6 was not available/run and API services were unavailable. |
| Hosted CI not run | Exact GitHub runner/build result is unknown | Workflow updated locally; no GitHub Actions run evidence. |
| Fresh frontend container image build unavailable | Current local production bundle build does not prove Compose image build | Earlier registry metadata timeout is in Sprint 4 evidence; this session did not have Docker. |
| Cold-start script removes named volumes | It permanently deletes local Postgres and Grafana data | Guarded by `--confirm-volume-destroy`; script was not run. |

Historical Sprints 1–3 evidence remains in their reports. It is not evidence that current uncommitted changes passed live runtime checks.
