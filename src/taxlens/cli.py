"""Command-line entry point: `uv run taxlens --help`."""

import httpx
import typer

from taxlens.config import settings
from taxlens.db import connect
from taxlens.ingest.crawl import run_crawl
from taxlens.ingest.extract import run_extract, redetect_review_dates

app = typer.Typer(no_args_is_help=True)


@app.command()
def check() -> None:
    """Confirm the database is reachable and the week 1 schema is in place."""
    with connect() as conn:
        version = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        row = version.fetchone()
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ).fetchall()
    typer.echo(f"pgvector: {row[0] if row else 'NOT INSTALLED'}")
    typer.echo("tables: " + ", ".join(t[0] for t in tables))


@app.command()
def crawl() -> None:
    """Week 1 task: fetch the manual index, download new or changed PDFs."""
    headers = {"User-Agent": settings.user_agent}
    with (
        httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client,
        connect() as conn,
    ):
        new, unchanged, failed = run_crawl(client, conn)
    typer.echo(f"new: {new}, unchanged: {unchanged}, failed: {failed}")


@app.command()
def extract() -> None:
    """Week 1 task: extract page-level text from stored PDFs into the pages table."""
    with connect() as conn:
        done, failed = run_extract(conn)
    typer.echo(f"extracted: {done}, failed: {failed}")

@app.command()
def review_dates() -> None:
    """Re-detect review dates from stored page text, without re-reading PDFs."""
    with connect() as conn:
        found, not_found = redetect_review_dates(conn)
    typer.echo(f"found: {found}, not found: {not_found}")


if __name__ == "__main__":
    app()
