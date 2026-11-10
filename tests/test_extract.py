from pathlib import Path

import pymupdf
import pytest

from taxlens.ingest.extract import extract_pages, find_last_reviewed

# The real first page of Part 02-02-03a, as PyMuPDF extracted it.
REAL_FIRST_PAGE = """\
Tax and Duty Manual
                                                                        Part 02-02-03a
The information in this document is provided as a guide only and
is not professional advice, including legal advice. It should not be
assumed that the guidance is comprehensive or that it provides a
definitive answer in every case.
1
Tax Treatment of Certain Dividends
Part 02-02-03a
This document should be read in conjunction with section 21B of the Taxes
Consolidation Act 1997
Document last reviewed February 2025
________________________________________________________________________
"""


def test_find_last_reviewed_on_a_real_first_page() -> None:
    assert find_last_reviewed(REAL_FIRST_PAGE) == "February 2025"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Document last reviewed February 2025", "February 2025"),
        ("This document was last reviewed December 2024", "December 2024"),
        ("Document last reviewed\nMarch 2023", "March 2023"),  # PDF line break mid-phrase
        ("DOCUMENT LAST REVIEWED JUNE 2022", "JUNE 2022"),  # case doesn't matter
        ("This manual has no review date at all.", None),
    ],
)
def test_find_last_reviewed_wordings(text: str, expected: str | None) -> None:
    assert find_last_reviewed(text) == expected


def make_pdf(path: Path, page_texts: list[str]) -> None:
    """Write a small PDF with one page per string, so tests don't need a real manual."""
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_extract_pages_returns_one_string_per_page_in_order(tmp_path: Path) -> None:
    pdf = tmp_path / "sample.pdf"
    make_pdf(pdf, ["First page text", "Second page text", "Third page text"])

    pages = extract_pages(str(pdf))

    assert len(pages) == 3
    assert "First page text" in pages[0]
    assert "Second page text" in pages[1]
    assert "Third page text" in pages[2]
