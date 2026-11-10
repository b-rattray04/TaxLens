from collections.abc import Iterator
from pathlib import Path

import pymupdf
import pytest

from taxlens.db import connect
from taxlens.ingest.extract import run_extract

FAKE_URL = "https://test.invalid/tdm/part-01/01-00-01.pdf"


def make_pdf(path: Path, page_texts: list[str]) -> None:
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


@pytest.fixture
def clean_db() -> Iterator[None]:
    """run_extract commits, so delete the fake document afterwards (pages cascade)."""
    yield
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE url LIKE 'https://test.invalid/%'")


@pytest.mark.db
@pytest.mark.usefixtures("clean_db")
def test_run_extract_stores_pages_once_and_skips_broken_files(tmp_path: Path) -> None:
    good = tmp_path / "good.pdf"
    make_pdf(good, ["Document last reviewed February 2025", "Second page"])
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"this is not a pdf")

    with connect() as conn:
        doc_row = conn.execute(
            "INSERT INTO documents (url) VALUES (%s) RETURNING id", (FAKE_URL,)
        ).fetchone()
        assert doc_row is not None
        for i, path in enumerate([good, broken]):
            conn.execute(
                "INSERT INTO document_versions (document_id, content_hash, storage_path) "
                "VALUES (%s, %s, %s)",
                (doc_row[0], f"hash-{i}", str(path)),
            )
        conn.commit()

        # Other versions may exist from a real crawl; only check our two.
        done, failed = run_extract(conn)
        assert failed >= 1

        rows = conn.execute(
            "SELECT v.storage_path, v.page_count, v.last_reviewed, count(p.page_no) "
            "FROM document_versions v LEFT JOIN pages p ON p.version_id = v.id "
            "WHERE v.document_id = %s GROUP BY v.id ORDER BY v.id",
            (doc_row[0],),
        ).fetchall()
        assert rows == [
            (str(good), 2, "February 2025", 2),
            (str(broken), None, None, 0),
        ]

        # A second run doesn't duplicate pages for the good PDF.
        run_extract(conn)
        count = conn.execute(
            "SELECT count(*) FROM pages p JOIN document_versions v ON v.id = p.version_id "
            "WHERE v.storage_path = %s",
            (str(good),),
        ).fetchone()
        assert count == (2,)
