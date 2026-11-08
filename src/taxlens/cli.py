"""Command-line entry point: `uv run taxlens --help`."""

import typer

from taxlens.db import connect

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
    raise NotImplementedError("Week 1: implement in taxlens/ingest/crawl.py")


@app.command()
def extract() -> None:
    """Week 1 task: extract page-level text from stored PDFs into the pages table."""
    raise NotImplementedError("Week 1: implement in taxlens/ingest/extract.py")


if __name__ == "__main__":
    app()
