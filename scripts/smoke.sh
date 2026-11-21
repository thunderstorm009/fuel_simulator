#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env.example ]]; then
  python3 scripts/check_compose_env.py --env-file .env.example
else
  python3 scripts/check_compose_env.py
fi

if [[ "${SMOKE_SKIP_BUILD:-0}" == "1" ]]; then
  docker compose up -d
else
  docker compose up --build -d
fi
services=(simulator postgres api worker predictor frontend prometheus grafana)
frontend_port=$(docker compose config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["services"]["frontend"]["ports"][0]["published"])')
for _ in $(seq 1 60); do
  healthy=1
  for service in "${services[@]}"; do
    state=$(docker compose ps --format json "$service" | python3 -c 'import json,sys; rows=[json.loads(x) for x in sys.stdin if x.strip()]; print(rows[0].get("Health", "") if rows else "missing")')
    if [ "$state" != "healthy" ]; then healthy=0; break; fi
  done
  if [ "$healthy" -eq 1 ]; then
    curl --fail --silent http://localhost:8000/v1/health
    curl --fail --silent http://localhost:8101/health
    curl --fail --silent http://localhost:8102/health
    curl --fail --silent http://localhost:8103/health
    curl --fail --silent "http://localhost:${frontend_port}/" >/dev/null
    exit 0
  fi
  sleep 2
done
docker compose ps
docker compose logs --no-color --tail=100
exit 1
