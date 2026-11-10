from pathlib import Path

import httpx
import pytest

from taxlens.config import settings
from taxlens.ingest.crawl import (
    INDEX_URL,
    TDM,
    current_pdf_urls,
    discover_pdf_urls,
    part_from_url,
    part_page_urls,
    sha256,
)

FIXTURES = Path(__file__).parent / "fixtures"  # look at the folder the test file is in
html = (FIXTURES / "part01_snippet.html").read_text()


def test_part_from_url() -> None:
    url = (
        "https://www.revenue.ie/en/tax-professionals/tdm/"
        "income-tax-capital-gains-tax-corporation-tax/part-04/04-08-11.pdf"
    )
    assert part_from_url(url) == "04-08-11"


def test_part_from_url_rejects_non_pdf() -> None:
    assert part_from_url("https://www.revenue.ie/en/index.aspx") is None


def test_sha256_is_stable() -> None:
    assert sha256(b"abc") == sha256(b"abc")
    assert sha256(b"abc") != sha256(b"abd")


def test_current_pdf_urls_ignore_older_versions() -> None:
    html = (FIXTURES / "part01_snippet.html").read_text()
    base_url = "https://www.revenue.ie/en/tax-professionals/tdm/income-tax-capital-gains-tax-corporation-tax/part-01/index.aspx"

    result = current_pdf_urls(html, base_url)

    assert result == [
        "https://www.revenue.ie/en/tax-professionals/tdm/income-tax-capital-gains-tax-corporation-tax/part-01/01-00-02.pdf",
    ]


def test_part_page_urls_lists_every_part() -> None:
    html = (FIXTURES / "index_snippet.html").read_text()
    base_url = f"https://www.revenue.ie{TDM}/index.aspx"

    result = part_page_urls(html, base_url)

    assert result == [
        f"https://www.revenue.ie{TDM}/misc/index.aspx",
        f"https://www.revenue.ie{TDM}/part-01/index.aspx",
        f"https://www.revenue.ie{TDM}/part-02/index.aspx",
        f"https://www.revenue.ie{TDM}/part-04/index.aspx",
        f"https://www.revenue.ie{TDM}/part-04a/index.aspx",
    ]


PART01 = "/en/tax-professionals/tdm/income-tax-capital-gains-tax-corporation-tax/part-01"


def test_current_pdf_urls_returns_every_current_pdf() -> None:
    html = f"""
    <div>
      <a class="pdf" href="{PART01}/01-00-02.pdf">Part 01-00-02</a>
      <p class="older-versions">
        <a href="{PART01}/01-00-02-20211111095623.pdf">11-Nov-2021</a>
      </p>
      <a class="pdf" href="{PART01}/01-00-04.pdf">Part 01-00-04</a>
      <a class="pdf">No href</a>
    </div>
    """
    base_url = f"https://www.revenue.ie{PART01}/index.aspx"

    result = current_pdf_urls(html, base_url)

    assert result == [
        f"https://www.revenue.ie{PART01}/01-00-02.pdf",
        f"https://www.revenue.ie{PART01}/01-00-04.pdf",
    ]


SITE = "https://www.revenue.ie"

# A tiny fake Revenue site: one index page and two Part pages.
FAKE_PAGES = {
    INDEX_URL: f"""
        <ul>
          <li class="liclikable"><a href="{TDM}/part-01/index.aspx">Part 01</a></li>
          <li class="liclikable"><a href="{TDM}/part-02/index.aspx">Part 02</a></li>
        </ul>
    """,
    f"{SITE}{TDM}/part-01/index.aspx": f"""
        <a class="pdf" href="{TDM}/part-01/01-00-01.pdf">Part 01-00-01</a>
        <p class="older-versions">
          <a href="{TDM}/part-01/01-00-01-20211111095623.pdf">11-Nov-2021</a>
        </p>
    """,
    f"{SITE}{TDM}/part-02/index.aspx": f"""
        <a class="pdf" href="{TDM}/part-02/02-01-01.pdf">Part 02-01-01</a>
        <a class="pdf" href="{TDM}/part-02/02-01-02.pdf">Part 02-01-02</a>
    """,
}


def fake_site(request: httpx.Request) -> httpx.Response:
    """Answer requests from FAKE_PAGES instead of the internet; anything else is a 404."""
    html = FAKE_PAGES.get(str(request.url))
    if html is None:
        return httpx.Response(404)
    return httpx.Response(200, text=html)


def test_discover_pdf_urls_follows_index_to_part_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "request_delay_seconds", 0)  # no real sleeping in tests
    client = httpx.Client(transport=httpx.MockTransport(fake_site))

    result = discover_pdf_urls(client)

    assert result == [
        f"{SITE}{TDM}/part-01/01-00-01.pdf",
        f"{SITE}{TDM}/part-02/02-01-01.pdf",
        f"{SITE}{TDM}/part-02/02-01-02.pdf",
    ]
