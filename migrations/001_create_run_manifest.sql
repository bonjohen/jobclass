-- Initial schema: run_manifest table for pipeline observability
CREATE TABLE IF NOT EXISTS run_manifest (
    run_id              TEXT PRIMARY KEY,
    pipeline_name       TEXT NOT NULL,
    dataset_name        TEXT NOT NULL,
    source_name         TEXT NOT NULL,
    source_url          TEXT,
    source_release_id   TEXT,
    downloaded_at       TIMESTAMPTZ,
    parser_name         TEXT,
    parser_version      TEXT,
    raw_checksum        TEXT,
    row_count_raw       INTEGER,
    row_count_stage     INTEGER,
    row_count_loaded    INTEGER,
    load_status         TEXT,
    failure_classification TEXT,
    validation_summary  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);
