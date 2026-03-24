-- Migration 011: O*NET Education & Training — staging, dimension, and bridge tables.

-- Staging table (different from other descriptors: has category column, no CI bounds)
CREATE TABLE IF NOT EXISTS stage__onet__education (
    occupation_code   TEXT NOT NULL,
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    scale_id          TEXT NOT NULL,
    category          INTEGER NOT NULL,
    category_label    TEXT,
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

-- Dimension table (keyed on element_id + category for education levels)
CREATE SEQUENCE IF NOT EXISTS seq_education_key START 1;
CREATE TABLE IF NOT EXISTS dim_education_requirement (
    education_key     INTEGER PRIMARY KEY DEFAULT nextval('seq_education_key'),
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    scale_id          TEXT NOT NULL,
    category          INTEGER NOT NULL,
    category_label    TEXT,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

-- Bridge table (occupation ↔ education requirement)
CREATE TABLE IF NOT EXISTS bridge_occupation_education (
    occupation_key    INTEGER NOT NULL,
    education_key     INTEGER NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);
