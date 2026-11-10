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
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser


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


def discover_pdf_urls() -> list[str]:
    raise NotImplementedError


def fetch_pdf(url: str) -> bytes:
    raise NotImplementedError


def store_if_new(url: str, data: bytes) -> bool:
    """Return True if this was a new version and was stored."""
    raise NotImplementedError
