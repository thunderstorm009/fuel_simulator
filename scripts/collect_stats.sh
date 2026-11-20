#!/usr/bin/env bash
set -euo pipefail

output="${1:-docs/results/docker-stats.csv}"
mkdir -p "$(dirname "$output")"
echo 'timestamp,container,cpu_percent,memory_usage,memory_limit' > "$output"
while [[ "${STOP_STATS:-0}" != "1" ]]; do
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}' | \
    while IFS=, read -r name cpu memory; do
      printf '%s,%s,%s,%s\n' "$timestamp" "$name" "$cpu" "$memory" >> "$output"
    done
  sleep 2
done
