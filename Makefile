.PHONY: up down test frontend-test typecheck lint smoke

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
