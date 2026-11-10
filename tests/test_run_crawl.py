from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from taxlens.config import settings
from taxlens.db import connect
from taxlens.ingest import crawl
from taxlens.ingest.crawl import run_crawl

# A made-up host, so test rows can never be mixed up with real Revenue data.
FAKE = "https://test.invalid/tdm"


def fake_site(request: httpx.Request) -> httpx.Response:
    """One index page, one Part page, and three PDFs: one good, one HTML, one missing."""
    pages = {
        f"{FAKE}/index.aspx": '<li class="liclikable"><a href="part-01/index.aspx">P1</a></li>',
        f"{FAKE}/part-01/index.aspx": (
            '<a class="pdf" href="01-00-01.pdf">good</a>'
            '<a class="pdf" href="01-00-02.pdf">html page</a>'
            '<a class="pdf" href="01-00-03.pdf">missing</a>'
        ),
    }
    url = str(request.url)
    if url in pages:
        return httpx.Response(200, text=pages[url])
    if url.endswith("01-00-01.pdf"):
        return httpx.Response(
            200, content=b"%PDF fake", headers={"content-type": "application/pdf"}
        )
    if url.endswith("01-00-02.pdf"):
        return httpx.Response(200, text="<html>oops</html>", headers={"content-type": "text/html"})
    return httpx.Response(404)


@pytest.fixture
def clean_db() -> Iterator[None]:
    """run_crawl commits, so a rollback can't undo it: delete the fake rows instead."""
    yield
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE url LIKE %s", (f"{FAKE}/%",))
        conn.execute("DELETE FROM fetch_log WHERE url LIKE %s", (f"{FAKE}/%",))


@pytest.mark.db
@pytest.mark.usefixtures("clean_db")
def test_run_crawl_counts_failures_and_is_a_no_op_second_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "request_delay_seconds", 0)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(crawl, "INDEX_URL", f"{FAKE}/index.aspx")
    client = httpx.Client(transport=httpx.MockTransport(fake_site))

    with connect() as conn:
        assert run_crawl(client, conn) == (1, 0, 2)  # new, unchanged, failed
        assert run_crawl(client, conn) == (0, 1, 2)  # second run stores nothing new

        log = conn.execute(
            "SELECT url, status_code, error IS NOT NULL FROM fetch_log "
            "WHERE url LIKE %s ORDER BY id",
            (f"{FAKE}/%",),
        ).fetchall()

    # Exactly one log row per PDF per run: no extra "200" row after a failure.
    first_run = [(u.rsplit("/", 1)[-1], code, has_error) for u, code, has_error in log[:3]]
    assert first_run == [
        ("01-00-01.pdf", 200, False),
        ("01-00-02.pdf", None, True),
        ("01-00-03.pdf", 404, True),
    ]
    assert len(log) == 6
