"""Week 1: extract text page by page so later citations can point to a page.

Use PyMuPDF (`import pymupdf`): `doc = pymupdf.open(path)`, then `page.get_text()` per page.
Also look for the "last reviewed" line near the start of each manual and store it on
document_versions. Keep page numbers 1-based to match what a reader sees in a PDF viewer.
"""

import re
import sys

import psycopg
import pymupdf


def extract_pages(pdf_path: str) -> list[str]:
    """Return the text of each page, in order."""
    pages: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            pages.append(page.get_text())
    return pages


def find_last_reviewed(first_pages_text: str) -> str | None:
    """Return the 'last reviewed' text as printed, or None if not found."""
    match = re.search(r"last reviewed\s+(\w+ \d{4})", first_pages_text, re.IGNORECASE)
    if match is None:
        return None
    return match.group(1)


def run_extract(conn: psycopg.Connection) -> tuple[int, int]:
    """Extract page text for every stored version that has none yet. Return (done, failed)."""
    versions = conn.execute(
        "SELECT v.id, v.storage_path FROM document_versions v "
        "WHERE NOT EXISTS (SELECT 1 FROM pages p WHERE p.version_id = v.id) "
        "ORDER BY v.id"
    ).fetchall()
    done = failed = 0

    for version_id, storage_path in versions:
        try:
            pages = extract_pages(storage_path)
            for page_no, text in enumerate(pages, start=1):
                conn.execute(
                    "INSERT INTO pages (version_id, page_no, text) VALUES (%s, %s, %s)",
                    (version_id, page_no, text.replace("\x00", "")),
                )
            conn.execute(
                "UPDATE document_versions SET last_reviewed = %s, page_count = %s WHERE id = %s",
                (find_last_reviewed("\n".join(pages[:2])), len(pages), version_id),
            )
            conn.commit()
            done += 1
        except Exception as e:
            conn.rollback()
            print(f"failed: version {version_id} ({storage_path}): {e}", file=sys.stderr)
            failed += 1

    return done, failed
