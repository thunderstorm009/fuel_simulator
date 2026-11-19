# Operations (planned)
- Start: make up (docker compose up -d). Stop: make down. Clean start: docker compose down -v then up.
- Services: simulator :8000, api, worker, predictor, frontend, postgres, prometheus, grafana.
- Config: every variable in .env.example (copy to .env). Never commit .env.
- Rollback: check out an earlier git tag (sprint-N) and rebuild images.
- Runbook entries (Sprint 6, D4): simulator unavailable, breaker open, stale data, SSE disconnected, predictor down, worker down, database down, malformed data, high simulator rejection rate, recommendation backlog, API latency high, snapshot table growing.
