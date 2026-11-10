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
import time
from urllib.parse import urljoin

import httpx
import psycopg
from selectolax.lexbor import LexborHTMLParser

from taxlens.config import settings


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
    tree = LexborHTMLParser(part_html)  # parse html string into searchable tree
    nodes = tree.css("a.pdf")  # select every <a> element with class "pdf"
    urls: list[str] = []  # collect results here
    # for each selected element, read its href (skip if there isn't one)
    for node in nodes:
        href = node.attributes.get("href")  # read this nodes href
        if href is None:
            continue  # skip links with no href
        urls.append(urljoin(base_url, href))  # the absolute url
    return urls


def part_page_urls(part_html: str, base_url: str) -> list[str]:
    tree = LexborHTMLParser(part_html)
    # find li elements with class liclikable, the the a elements inside them
    nodes = tree.css("li.liclikable a")
    urls: list[str] = []
    for node in nodes:
        href = node.attributes.get("href")
        if href is None:
            continue
        urls.append(urljoin(base_url, href))
    return urls


TDM = "/en/tax-professionals/tdm/income-tax-capital-gains-tax-corporation-tax"
INDEX_URL = f"https://www.revenue.ie{TDM}/index.aspx"


def get_html(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    response.raise_for_status()
    time.sleep(settings.request_delay_seconds)
    return response.text


def discover_pdf_urls(client: httpx.Client) -> list[str]:
    index_html = get_html(client, INDEX_URL)
    part_urls = part_page_urls(index_html, INDEX_URL)

    pdf_urls: list[str] = []
    for part_url in part_urls:
        part_html = get_html(client, part_url)
        result = current_pdf_urls(part_html, part_url)
        pdf_urls.extend(result)
    return pdf_urls


def fetch_pdf(client: httpx.Client, url: str) -> bytes:
    response = client.get(url)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/pdf" not in content_type:
        raise ValueError(f"Expected a PDF from {url}, got {content_type!r}")
    time.sleep(settings.request_delay_seconds)
    return response.content


def store_if_new(conn: psycopg.Connection, url: str, data: bytes) -> bool:
    """Return True if this was a new version and was stored."""
    content_hash = sha256(data)

    row = conn.execute("SELECT id FROM documents WHERE url = %s", (url,)).fetchone()
    if row is None:
        row = conn.execute(
            "INSERT INTO documents (url, part) VALUES (%s, %s) RETURNING id",
            (url, part_from_url(url)),
        ).fetchone()
    assert row is not None
    document_id = row[0]

    existing = conn.execute(
        "SELECT id FROM document_versions WHERE document_id = %s AND content_hash = %s",
        (document_id, content_hash),
    ).fetchone()
    if existing is not None:
        return False

    path = settings.data_dir / "pdfs" / f"{content_hash}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    conn.execute(
        "INSERT INTO document_versions (document_id, content_hash, storage_path) "
        "VALUES (%s, %s, %s)",
        (document_id, content_hash, str(path)),
    )

    return True
