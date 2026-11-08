# TaxLens

Question answering over Irish Revenue's Tax and Duty Manuals, with page-level citations and an evaluation harness.

> Not tax advice. Answers are generated from public Revenue guidance and may be wrong or out of date.

## Status

Week 1: ingestion pipeline (crawl, store, extract page text).

## Quickstart

Needs Docker and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
docker compose up -d --wait   # Postgres 17 + pgvector
uv sync                       # creates .venv and installs dependencies
uv run taxlens check          # should list pgvector and four tables
uv run pytest                 # all tests
```

`make up`, `make check`, `make test-all` and friends wrap these on Linux and macOS.

After editing anything in `db/init/`, run `docker compose down -v && docker compose up -d --wait` (or `make reset`). The init scripts only run on an empty database.

## Layout

```
db/init/            schema, applied when the database volume is first created
src/taxlens/
  config.py         settings from .env
  db.py             connection helper
  cli.py            `taxlens` command
  ingest/           week 1: crawl.py, extract.py
tests/              unit tests; tests marked `db` need Postgres running
data/               downloaded PDFs (git-ignored)
```
