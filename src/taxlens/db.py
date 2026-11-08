"""Database connection helper."""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from taxlens.config import settings


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Open a connection that commits on success and rolls back on error."""
    with psycopg.connect(settings.database_url) as conn:
        yield conn
