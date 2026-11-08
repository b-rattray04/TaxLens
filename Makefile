.PHONY: up down reset psql check test test-all lint

up:        ## Start Postgres and wait until it's healthy
	docker compose up -d --wait

down:      ## Stop Postgres, keep data
	docker compose down

reset:     ## Wipe the database and re-run db/init/*.sql
	docker compose down -v
	docker compose up -d --wait

psql:      ## Open a SQL shell in the container
	docker compose exec db psql -U taxlens -d taxlens

check:     ## Confirm pgvector and tables exist
	uv run taxlens check

test:      ## Unit tests only (no database needed)
	uv run pytest -m "not db"

test-all:  ## All tests, including database tests
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check . && uv run mypy
