from pathlib import Path

from taxlens.ingest.crawl import current_pdf_urls, part_from_url, sha256

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
