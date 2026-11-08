-- Week 1 schema: documents, their versions, and page-level text.
-- Chunks and embeddings arrive in week 2; the extension is enabled now so nothing changes later.

CREATE EXTENSION IF NOT EXISTS vector;

-- One row per manual, identified by its canonical URL.
CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT        NOT NULL UNIQUE,
    part        TEXT,                       -- e.g. '04-08-11', parsed from the URL
    title       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per distinct PDF we have seen for a manual. A re-fetch with the same
-- hash adds nothing, which is what makes a second crawl a no-op.
CREATE TABLE document_versions (
    id             BIGSERIAL PRIMARY KEY,
    document_id    BIGINT      NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    content_hash   TEXT        NOT NULL,    -- sha256 of the PDF bytes
    last_reviewed  TEXT,                    -- as printed in the manual; normalise later
    storage_path   TEXT        NOT NULL,    -- where the PDF lives under data/
    page_count     INT,
    fetched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, content_hash)
);

-- Extracted text, one row per page, so citations can point at a page.
CREATE TABLE pages (
    version_id  BIGINT NOT NULL REFERENCES document_versions (id) ON DELETE CASCADE,
    page_no     INT    NOT NULL,            -- 1-based, matching the PDF viewer
    text        TEXT   NOT NULL,
    PRIMARY KEY (version_id, page_no)
);

-- Every HTTP fetch, successful or not. Useful for debugging and for being a polite crawler.
CREATE TABLE fetch_log (
    id           BIGSERIAL PRIMARY KEY,
    url          TEXT        NOT NULL,
    status_code  INT,
    error        TEXT,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
