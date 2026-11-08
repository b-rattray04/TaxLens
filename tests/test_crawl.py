from taxlens.ingest.crawl import part_from_url, sha256


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
