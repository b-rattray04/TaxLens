"""Week 1: discover manual PDFs and download new or changed ones.

Suggested order:
1. `discover_pdf_urls`: start from the Income Tax / CGT / Corporation Tax manual index on
   revenue.ie, follow links to each Part, and collect the .pdf URLs. Check robots.txt first.
2. `fetch_pdf`: GET with `settings.user_agent`, sleep `settings.request_delay_seconds`
   between requests, log every fetch to `fetch_log`.
3. `store_if_new`: sha256 the bytes; if (document, hash) already exists do nothing,
   otherwise save under data/ and insert a document_versions row.

Done when every in-scope manual is stored and a second run downloads nothing new.
"""

import hashlib


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def part_from_url(url: str) -> str | None:
    """Extract the Part number from a manual URL, e.g. '.../part-04/04-08-11.pdf' -> '04-08-11'."""
    name = url.rstrip("/").rsplit("/", 1)[-1]
    if not name.lower().endswith(".pdf"):
        return None
    return name[:-4]

def current_pdf_urls(part_html: str, base_url: str) -> list[str]:
    """Return absolute URLs of the current PDFs on a Part page"""
    raise NotImplementedError

def discover_pdf_urls() -> list[str]:
    raise NotImplementedError


def fetch_pdf(url: str) -> bytes:
    raise NotImplementedError


def store_if_new(url: str, data: bytes) -> bool:
    """Return True if this was a new version and was stored."""
    raise NotImplementedError
