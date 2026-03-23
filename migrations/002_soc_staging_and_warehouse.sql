-- Phase 3: SOC staging tables, dim_occupation, bridge_occupation_hierarchy

-- Staging tables
CREATE TABLE IF NOT EXISTS stage__soc__hierarchy (
    soc_code            TEXT NOT NULL,
    occupation_title    TEXT NOT NULL,
    occupation_level    INTEGER NOT NULL,
    occupation_level_name TEXT NOT NULL,
    parent_soc_code     TEXT,
    source_release_id   TEXT NOT NULL,
    parser_version      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stage__soc__definitions (
    soc_code            TEXT NOT NULL,
    occupation_definition TEXT NOT NULL,
    source_release_id   TEXT NOT NULL,
    parser_version      TEXT NOT NULL
);

-- Core warehouse dimension
CREATE TABLE IF NOT EXISTS dim_occupation (
    occupation_key      INTEGER PRIMARY KEY,
    soc_code            TEXT NOT NULL,
    occupation_title    TEXT NOT NULL,
    occupation_level    INTEGER NOT NULL,
    occupation_level_name TEXT NOT NULL,
    parent_soc_code     TEXT,
    major_group_code    TEXT,
    minor_group_code    TEXT,
    broad_occupation_code TEXT,
    detailed_occupation_code TEXT,
    occupation_definition TEXT,
    soc_version         TEXT NOT NULL,
    is_leaf             BOOLEAN NOT NULL DEFAULT false,
    effective_start_date TEXT,
    effective_end_date  TEXT,
    is_current          BOOLEAN NOT NULL DEFAULT true,
    source_release_id   TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_occupation_bk
    ON dim_occupation (soc_code, soc_version);

-- Core warehouse bridge
CREATE TABLE IF NOT EXISTS bridge_occupation_hierarchy (
    parent_occupation_key INTEGER NOT NULL,
    child_occupation_key  INTEGER NOT NULL,
    relationship_level   INTEGER NOT NULL,
    soc_version         TEXT NOT NULL,
    source_release_id   TEXT NOT NULL,
    PRIMARY KEY (parent_occupation_key, child_occupation_key, soc_version)
);

-- Sequence for dim_occupation surrogate keys
CREATE SEQUENCE IF NOT EXISTS seq_occupation_key START 1;
