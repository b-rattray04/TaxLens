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
        # Other wordings found in the crawled manuals
        ("Document last updated May 2026", "May 2026"),
        ("This document was last updated in May 2026", "May 2026"),
        ("Document last reviewed in January 2024", "January 2024"),
        ("Document updated last October 2024", "October 2024"),
        ("Document reviewed September 2024", "September 2024"),
        # Must not match: "updated" followed by something that isn't a date
        ("Section 21B was updated by Finance Act 2024", None),
        ("Document last updated on 27 June 2017", "June 2017"),
        ("Document reviewed September2025", "September2025"),  # missing space in the PDF
        ("Summary of ROS panels updated in 2020 Form 11", None),
        ("The rate band and the rate of USC is updated for 2020.", None),
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
