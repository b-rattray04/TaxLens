"""Week 1: extract text page by page so later citations can point to a page.

Use PyMuPDF (`import pymupdf`): `doc = pymupdf.open(path)`, then `page.get_text()` per page.
Also look for the "last reviewed" line near the start of each manual and store it on
document_versions. Keep page numbers 1-based to match what a reader sees in a PDF viewer.
"""

import re

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
