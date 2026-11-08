import pytest

from taxlens.db import connect

pytestmark = pytest.mark.db


def test_schema_present() -> None:
    with connect() as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ).fetchall()
    tables = {r[0] for r in rows}
    assert {"documents", "document_versions", "pages", "fetch_log"} <= tables


def test_duplicate_version_rejected() -> None:
    """The unique (document_id, content_hash) constraint is what makes re-crawls a no-op."""
    with connect() as conn:
        row = conn.execute(
            "INSERT INTO documents (url) VALUES ('test://dup') RETURNING id"
        ).fetchone()
        assert row is not None
        doc_id = row[0]
        insert = (
            "INSERT INTO document_versions (document_id, content_hash, storage_path) "
            "VALUES (%s, 'h1', 'x') ON CONFLICT DO NOTHING RETURNING id"
        )
        assert conn.execute(insert, (doc_id,)).fetchone() is not None
        assert conn.execute(insert, (doc_id,)).fetchone() is None
        conn.rollback()
