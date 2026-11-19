# Final demo script (8-10 minutes; finalise in Sprint 7 with exact commands)
1. docker compose up from scratch; show the health panel (HEALTHY).
2. Normal operations: inventory, risk matrix, SIMULATED badge.
3. Inject a demand spike on Dhaka: risk rises, forecast shows hours to stockout.
4. Open a recommendation: drivers, constraints, before and after risk, alternatives. Approve it.
5. Show the shipment in the simulator allocations and arrival; risk falls.
6. Inject a route disruption: reroute through another depot.
7. Inject an API fault: degraded banner, alerts, cached state still works; clear it and show recovery.
8. Stop the predictor: fallback, low confidence, fallback metric. Restart it.
9. Show Grafana, the policy comparison table and load-test numbers.
10. State limitations honestly.
Roles: driver, narrator, fault injector. Keep a backup recording. If a step fails, use the recovery line in the final version of this file.
