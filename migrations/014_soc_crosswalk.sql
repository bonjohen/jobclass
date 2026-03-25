-- Migration 014: SOC 2010↔2018 crosswalk bridge table.

-- Staging table for crosswalk data
CREATE TABLE IF NOT EXISTS stage__soc__crosswalk (
    source_soc_code      TEXT NOT NULL,
    source_soc_title     TEXT,
    source_soc_version   TEXT NOT NULL,
    target_soc_code      TEXT NOT NULL,
    target_soc_title     TEXT,
    target_soc_version   TEXT NOT NULL,
    mapping_type         TEXT NOT NULL,
    source_release_id    TEXT NOT NULL,
    parser_version       TEXT NOT NULL
);

-- Bridge table for SOC crosswalk mappings
CREATE SEQUENCE IF NOT EXISTS seq_crosswalk_key START 1;
CREATE TABLE IF NOT EXISTS bridge_soc_crosswalk (
    crosswalk_key        INTEGER PRIMARY KEY DEFAULT nextval('seq_crosswalk_key'),
    source_soc_code      TEXT NOT NULL,
    source_soc_version   TEXT NOT NULL,
    target_soc_code      TEXT NOT NULL,
    target_soc_version   TEXT NOT NULL,
    mapping_type         TEXT NOT NULL,
    source_release_id    TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_crosswalk_codes
    ON bridge_soc_crosswalk (source_soc_code, source_soc_version, target_soc_code, target_soc_version);
