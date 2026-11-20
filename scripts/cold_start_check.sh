#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "--confirm-volume-destroy" ]]; then
  echo 'This check deletes PostgreSQL and Grafana volumes. Re-run with --confirm-volume-destroy only when that local data is disposable.' >&2
  exit 2
fi
started=$(date +%s)
docker compose down -v
docker compose up --build -d
for service in simulator postgres api worker predictor frontend prometheus grafana; do
  for attempt in $(seq 1 60); do
    status=$(docker compose ps --format json "$service" | python3 -c 'import json,sys; rows=[json.loads(x) for x in sys.stdin if x.strip()]; print(rows[0].get("Health", "") if rows else "")')
    [[ "$status" == "healthy" ]] && break
    sleep 2
  done
  [[ "$status" == "healthy" ]] || { echo "$service did not become healthy" >&2; exit 1; }
done
for url in http://localhost:8101/health http://localhost:8102/health http://localhost:8103/health http://localhost:8101/api/health; do
  curl --fail --silent --show-error "$url" >/dev/null
done
echo "cold_start_elapsed_seconds=$(( $(date +%s) - started ))"
