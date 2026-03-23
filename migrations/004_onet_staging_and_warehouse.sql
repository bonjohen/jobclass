-- Migration 004: O*NET staging tables, descriptor dimensions, and bridge tables.

-- ============================================================
-- Staging tables (one per O*NET domain)
-- ============================================================

CREATE TABLE IF NOT EXISTS stage__onet__skills (
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

CREATE TABLE IF NOT EXISTS stage__onet__knowledge (
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

CREATE TABLE IF NOT EXISTS stage__onet__abilities (
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

CREATE TABLE IF NOT EXISTS stage__onet__tasks (
    occupation_code   TEXT NOT NULL,
    task_id           TEXT NOT NULL,
    task              TEXT NOT NULL,
    task_type         TEXT,
    incumbents_responding INTEGER,
    date              TEXT,
    domain_source     TEXT,
    source_release_id TEXT NOT NULL,
    parser_version    TEXT NOT NULL
);

-- ============================================================
-- Descriptor dimension tables
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS seq_skill_key START 1;
CREATE TABLE IF NOT EXISTS dim_skill (
    skill_key         INTEGER PRIMARY KEY DEFAULT nextval('seq_skill_key'),
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

CREATE SEQUENCE IF NOT EXISTS seq_knowledge_key START 1;
CREATE TABLE IF NOT EXISTS dim_knowledge (
    knowledge_key     INTEGER PRIMARY KEY DEFAULT nextval('seq_knowledge_key'),
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

CREATE SEQUENCE IF NOT EXISTS seq_ability_key START 1;
CREATE TABLE IF NOT EXISTS dim_ability (
    ability_key       INTEGER PRIMARY KEY DEFAULT nextval('seq_ability_key'),
    element_id        TEXT NOT NULL,
    element_name      TEXT NOT NULL,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

CREATE SEQUENCE IF NOT EXISTS seq_task_key START 1;
CREATE TABLE IF NOT EXISTS dim_task (
    task_key          INTEGER PRIMARY KEY DEFAULT nextval('seq_task_key'),
    task_id           TEXT NOT NULL,
    task              TEXT NOT NULL,
    task_type         TEXT,
    source_version    TEXT NOT NULL,
    is_current        BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Bridge tables (occupation ↔ descriptor)
-- ============================================================

CREATE TABLE IF NOT EXISTS bridge_occupation_skill (
    occupation_key    INTEGER NOT NULL,
    skill_key         INTEGER NOT NULL,
    scale_id          TEXT NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bridge_occupation_knowledge (
    occupation_key    INTEGER NOT NULL,
    knowledge_key     INTEGER NOT NULL,
    scale_id          TEXT NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bridge_occupation_ability (
    occupation_key    INTEGER NOT NULL,
    ability_key       INTEGER NOT NULL,
    scale_id          TEXT NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bridge_occupation_task (
    occupation_key    INTEGER NOT NULL,
    task_key          INTEGER NOT NULL,
    data_value        DOUBLE,
    n                 INTEGER,
    source_version    TEXT NOT NULL,
    source_release_id TEXT NOT NULL,
    load_timestamp    TIMESTAMPTZ DEFAULT now()
);
