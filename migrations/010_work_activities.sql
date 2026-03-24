-- Migration 010: O*NET Work Activities — staging, dimension, and bridge tables.

-- Staging table (same schema as other O*NET descriptors)
CREATE TABLE IF NOT EXISTS stage__onet__work_activities (
    occupation_code   TEXT NOT NULL,
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    scale_id          TEXT NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    standard_error    DOUBLE,
    lower_ci          DOUBLE,
    upper_ci          DOUBLE,
    recommend_suppress BOOLEAN,
    not_relevant      BOOLEAN,
    date              TEXT,
    domain_source     TEXT,
    source_release_id TEXT NOT NULL,
    parser_version    TEXT NOT NULL
);

-- Dimension table
CREATE SEQUENCE IF NOT EXISTS seq_work_activity_key START 1;
CREATE TABLE IF NOT EXISTS dim_work_activity (
    work_activity_key INTEGER PRIMARY KEY DEFAULT nextval('seq_work_activity_key'),
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

-- Bridge table (occupation ↔ work activity)
CREATE TABLE IF NOT EXISTS bridge_occupation_work_activity (
    occupation_key    INTEGER NOT NULL,
    work_activity_key INTEGER NOT NULL,
    scale_id          TEXT NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);
