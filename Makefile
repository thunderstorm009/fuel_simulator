.PHONY: up down test frontend-test typecheck lint smoke test-e2e preflight demo demo-reset

up:
	docker compose up --build -d

down:
	docker compose down

test:
	pytest
	npm --prefix web run test

frontend-test:
	npm --prefix web run test

typecheck:
	npm --prefix web run typecheck

lint:
	ruff check .
	ruff format --check .
	npm --prefix web run typecheck
	npm --prefix web run build

smoke:
	bash scripts/smoke.sh

test-e2e:
	npm --prefix web run test:e2e

preflight:
	bash scripts/preflight_judging.sh

demo:
	python3 scripts/demo_director.py

demo-reset:
	curl -s -X POST http://localhost:8000/admin/reset && curl -s -X POST http://localhost:8000/admin/pause
