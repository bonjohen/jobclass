# New Data Source Integration — Design Document

## 1. Goal

Extend the JobClass warehouse with additional federal data sources and enrichment datasets that deepen occupation profiles, lengthen historical time-series, and add analytical dimensions the current system cannot support.

Every new source must integrate through the existing occupation-centered architecture. Occupation (`dim_occupation`, keyed on SOC code) remains the stable backbone. New data attaches to it — not the other way around.

## 2. Guiding Principles

All principles from the base design document remain in force:

- Immutable raw storage. Never overwrite downloaded artifacts.
- Idempotent loading. Re-running the same dataset version must not create duplicates.
- Fail-fast on schema drift. Block warehouse publication until parser is updated.
- Preserve source nulls. Never impute suppressed or missing values.
- Separate source release time from business reference time.
- Separate as-published from comparable history.
- Separate observed from derived metrics.

New principle for this phase:

- **Incremental integration.** Each new source must be independently deployable. No source depends on another new source being loaded first. The only hard dependency is the existing SOC taxonomy.

## 3. Scope Overview

This document covers seven integration targets organized into four tiers.

### Tier 1 — Surface Existing Data (No New Downloads)

These are already ingested into bridge tables but not exposed in the website.

| ID | Source | What It Adds |
|----|--------|-------------|
| DS-01 | O\*NET Knowledge | Knowledge domain scores on occupation profiles |
| DS-02 | O\*NET Abilities | Ability scores on occupation profiles |

### Tier 2 — New O\*NET Domains (Same Infrastructure)

Same TSV format, same parser pattern, same bridge table design.

| ID | Source | What It Adds |
|----|--------|-------------|
| DS-03 | O\*NET Work Activities | Generalized and detailed work activity scores |
| DS-04 | O\*NET Education & Training | Typical education level, experience, and training requirements |
| DS-05 | O\*NET Technology Skills | Tools and technology used by occupation |

### Tier 3 — BLS CPI (Inflation Adjustment)

Single national time-series. High analytical value, low integration complexity.

| ID | Source | What It Adds |
|----|--------|-------------|
| DS-06 | BLS CPI-U (All Urban Consumers) | Inflation-adjusted (real) wage time-series |

### Tier 4 — SOC Crosswalk (Historical Depth)

Enables pre-2018 OEWS vintages to be mapped into the current taxonomy.

| ID | Source | What It Adds |
|----|--------|-------------|
| DS-07 | SOC 2010↔2018 Crosswalk | Extends comparable history back to OEWS 2012 |

---

## 4. DS-01: Surface O\*NET Knowledge

### Current State

`bridge_occupation_knowledge` is already populated. `dim_knowledge` contains element IDs and names. The data exists in the warehouse but the occupation profile page and API do not expose it.

### Required Changes

**API:** Add `/api/occupations/{soc_code}/knowledge` endpoint in `src/jobclass/web/api/occupations.py`. Follow the same pattern as the existing `/skills` endpoint: query `bridge_occupation_knowledge` joined to `dim_knowledge` and `dim_occupation`, filter on `scale_id = 'IM'`, return element name and importance score, ordered by importance descending.

**Website:** Add a "Knowledge" section to the occupation profile page (`occupation.js`). Render a table identical to the skills table: columns for Knowledge Domain, Importance, and Level. Only display the section if the API returns data.

**Static site:** Add the knowledge endpoint to the per-occupation JSON generation in `build_static.py`.

**Tests:** Add a test for the new endpoint returning 200 with expected fields. Add a test for the occupation profile page containing the knowledge section.

### No New Downloads Required

The O\*NET knowledge data is already extracted, parsed, staged, and loaded by the existing pipeline.

---

## 5. DS-02: Surface O\*NET Abilities

Identical pattern to DS-01.

### Required Changes

**API:** Add `/api/occupations/{soc_code}/abilities` endpoint.

**Website:** Add an "Abilities" section to the occupation profile page.

**Static site:** Add the abilities endpoint to per-occupation JSON generation.

**Tests:** Mirror the knowledge tests.

---

## 6. DS-03: O\*NET Work Activities

### Source Description

O\*NET publishes two work activity files:

- **Generalized Work Activities** (`Work Activities.txt`) — 41 high-level activity categories (e.g., "Analyzing Data or Information", "Operating Vehicles"). Each occupation is rated on importance (IM) and level (LV) scales.
- **Detailed Work Activities** (`DWA Reference.txt` + `Tasks to DWAs.txt`) — ~2,000 specific activities linked to tasks. More granular but noisier.

Both files use the same TSV format as Skills, Knowledge, and Abilities: columns `O*NET-SOC Code`, `Element ID`, `Element Name`, `Scale ID`, `Data Value`, `N`, `Standard Error`, `Lower CI Bound`, `Upper CI Bound`, `Recommend Suppress`, `Not Relevant`, `Date`, `Domain Source`.

### Data Model

**New dimension:** `dim_work_activity` — same schema as `dim_skill`:

```
dim_work_activity
    work_activity_key   INTEGER PRIMARY KEY
    element_id          TEXT NOT NULL          -- e.g., "4.A.1.a.1"
    element_name        TEXT NOT NULL          -- e.g., "Analyzing Data or Information"
    source_version      TEXT NOT NULL
```

**New bridge:** `bridge_occupation_work_activity` — same schema as `bridge_occupation_skill`:

```
bridge_occupation_work_activity
    occupation_key      INTEGER NOT NULL       -- FK to dim_occupation
    work_activity_key   INTEGER NOT NULL       -- FK to dim_work_activity
    scale_id            TEXT NOT NULL           -- 'IM' or 'LV'
    data_value          DOUBLE
    n                   INTEGER
    source_version      TEXT NOT NULL
    source_release_id   TEXT NOT NULL
    load_timestamp      TIMESTAMPTZ
```

### Pipeline

**Manifest:** Add entry for `onet_work_activities` pointing to `https://www.onetcenter.org/dl_files/database/db_29_1_text/Work%20Activities.txt`.

**Parser:** Reuse `parse_onet_descriptors()` from `src/jobclass/parse/onet.py`. The file format is identical to Skills/Knowledge/Abilities.

**Loader:** Reuse `load_dim_descriptor()` and `load_bridge_occupation_descriptor()` patterns from `src/jobclass/load/onet.py`, parameterized for the work_activity dimension and bridge tables.

**Migration:** New SQL migration creating the dimension and bridge tables plus the `seq_work_activity_key` sequence.

**API, website, static site, tests:** Follow DS-01 pattern.

---

## 7. DS-04: O\*NET Education & Training

### Source Description

O\*NET publishes `Education, Training, and Experience.txt` with columns:

- `O*NET-SOC Code`
- `Element ID` — identifies the education/training category
- `Element Name` — e.g., "Required Level of Education"
- `Scale ID` — typically `RL` (required level)
- `Category` — ordinal value (e.g., 1–12 for education levels)
- `Data Value` — percentage of respondents at that level
- `N`, `Standard Error`, `Lower CI Bound`, `Upper CI Bound`
- `Recommend Suppress`, `Not Relevant`, `Date`, `Domain Source`

This differs from other O\*NET files because it uses a **category distribution** rather than a single importance score. Each occupation has multiple rows per element (one per category level), with `Data Value` representing the percentage of workers at that level.

### Data Model

**New dimension:** `dim_education_requirement`:

```
dim_education_requirement
    education_key       INTEGER PRIMARY KEY
    element_id          TEXT NOT NULL
    element_name        TEXT NOT NULL
    category            INTEGER NOT NULL       -- Ordinal level (1-12)
    category_label      TEXT                   -- e.g., "Bachelor's degree"
    source_version      TEXT NOT NULL
```

**New bridge:** `bridge_occupation_education`:

```
bridge_occupation_education
    occupation_key      INTEGER NOT NULL
    education_key       INTEGER NOT NULL
    scale_id            TEXT NOT NULL
    data_value          DOUBLE                 -- Percentage at this level
    n                   INTEGER
    source_version      TEXT NOT NULL
    source_release_id   TEXT NOT NULL
    load_timestamp      TIMESTAMPTZ
```

### Pipeline

**Manifest:** Add entry for `onet_education` pointing to `https://www.onetcenter.org/dl_files/database/db_29_1_text/Education%2C%20Training%2C%20and%20Experience.txt`.

**Parser:** New parser function `parse_onet_education()` in `onet.py`. Must handle the `Category` column that other O\*NET files don't have. Return dataclass rows with `category` and `data_value` (percentage).

**Loader:** New loader that creates dimension rows from distinct `(element_id, category)` combinations and bridge rows joining to occupation keys.

**API:** Add `/api/occupations/{soc_code}/education` endpoint. Return the category distribution — for each education element, show the percentage breakdown by level. The typical display is a summary showing the most common required education level.

**Website:** Add an "Education & Training" section to the occupation profile. Display the dominant education level as a summary, with a collapsible detail showing the full distribution.

---

## 8. DS-05: O\*NET Technology Skills

### Source Description

O\*NET publishes `Technology Skills.txt` with columns:

- `O*NET-SOC Code`
- `T2 Type` — category (e.g., "Tools", "Technology")
- `T2 Example` — specific tool or technology name (e.g., "Microsoft Excel", "Python")
- `Commodity Code` — UNSPSC code for the tool
- `Commodity Title` — UNSPSC description

This differs from other O\*NET files: it is a **flat list of tools per occupation** without importance/level scores. The data is categorical, not numeric.

### Data Model

**New dimension:** `dim_technology`:

```
dim_technology
    technology_key      INTEGER PRIMARY KEY
    commodity_code      TEXT                   -- UNSPSC code (may be null)
    commodity_title     TEXT
    t2_type             TEXT NOT NULL          -- 'Tools' or 'Technology'
    example_name        TEXT NOT NULL          -- e.g., "Microsoft Excel"
    source_version      TEXT NOT NULL
```

**New bridge:** `bridge_occupation_technology`:

```
bridge_occupation_technology
    occupation_key      INTEGER NOT NULL
    technology_key      INTEGER NOT NULL
    source_version      TEXT NOT NULL
    source_release_id   TEXT NOT NULL
    load_timestamp      TIMESTAMPTZ
```

Note: no `scale_id` or `data_value` — this is a binary association (occupation uses this tool or it doesn't).

### Pipeline

**Manifest:** Add entry for `onet_technology_skills` pointing to `https://www.onetcenter.org/dl_files/database/db_29_1_text/Technology%20Skills.txt`.

**Parser:** New parser function `parse_onet_technology()` in `onet.py`. Handle the different column structure (no Scale ID, Data Value, N, etc.).

**Loader:** Extract distinct technologies into `dim_technology`, then load the bridge.

**API:** Add `/api/occupations/{soc_code}/technology` endpoint. Return tools grouped by `t2_type`.

**Website:** Add a "Tools & Technology" section to the occupation profile. Display as a grouped list: "Tools" heading with tool names, "Technology" heading with technology names.

---

## 9. DS-06: BLS CPI-U (Inflation Adjustment)

### Source Description

The BLS Consumer Price Index for All Urban Consumers (CPI-U) is the standard deflator for converting nominal wages to real (inflation-adjusted) wages.

**Source URL:** `https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems`

This is a fixed-width or tab-delimited text file with columns:

- `series_id` — e.g., `CUSR0000SA0` (CPI-U, US city average, all items, seasonally adjusted)
- `year`
- `period` — `M01` through `M13` (M13 is annual average)
- `value` — CPI index value (base period = 100)

We need only the annual average (`M13`) for the national all-items series (`CUSR0000SA0`).

### Data Model

**New dimension table:** `dim_price_index`:

```
dim_price_index
    price_index_key     INTEGER PRIMARY KEY
    series_id           TEXT NOT NULL          -- BLS series identifier
    series_name         TEXT NOT NULL          -- Human-readable name
    base_period         TEXT NOT NULL          -- e.g., "1982-84=100"
    seasonally_adjusted BOOLEAN NOT NULL
    source_release_id   TEXT NOT NULL
```

**New fact table:** `fact_price_index_observation`:

```
fact_price_index_observation
    observation_key     INTEGER PRIMARY KEY
    price_index_key     INTEGER NOT NULL       -- FK to dim_price_index
    period_key          INTEGER NOT NULL       -- FK to dim_time_period
    index_value         DOUBLE NOT NULL        -- CPI index value
    source_release_id   TEXT NOT NULL
    run_id              TEXT
```

**New derived metrics in `dim_metric`:**

- `real_mean_annual_wage` — Mean annual wage deflated to a base year
- `real_median_annual_wage` — Median annual wage deflated to a base year

**Derivation formula:**

```
real_wage = nominal_wage × (CPI_base_year / CPI_observation_year)
```

Using 2023 as the base year: a 2021 wage of $100,000 with CPI 2021=270.97 and CPI 2023=304.70 becomes $100,000 × (304.70/270.97) = $112,448 in 2023 dollars.

### Pipeline

**Manifest:** Add entry for `bls_cpi` pointing to the CPI data file.

**Parser:** New `parse_cpi()` function in a new `src/jobclass/parse/cpi.py` module. Filter to series `CUSR0000SA0`, period `M13`, extract year and value.

**Loader:** Load `dim_price_index` (single row for the CPI-U series) and `fact_price_index_observation` (one row per year).

**Time-series integration:** Add a new derivation step in `timeseries_refresh.py` that computes `real_mean_annual_wage` and `real_median_annual_wage` by joining `fact_time_series_observation` (nominal wages) to `fact_price_index_observation` (CPI values) on period_key.

**API:** The existing `/api/trends/{soc_code}` endpoint already supports `metric` as a query parameter. No new endpoint needed — just register the new metric names in `dim_metric` and the trend explorer will expose them.

**Website:** Add "Real Mean Annual Wage" and "Real Median Annual Wage" to the metric dropdown in the Trend Explorer and Ranked Movers pages. No new pages required.

### CPI-Specific Considerations

- BLS CPI files use a fixed-width-ish format with tab separators and extra whitespace. The parser must strip padding.
- The CPI data goes back to 1913. We only need years overlapping with OEWS data (2012+).
- The base period (1982-84=100) is a BLS convention. We store the raw index values and compute deflation at query time or derivation time.
- CPI data is revised. The `source_release_id` tracks which vintage of CPI we downloaded.

---

## 10. DS-07: SOC 2010↔2018 Crosswalk

### Source Description

BLS publishes a crosswalk mapping SOC 2010 occupation codes to SOC 2018 codes. This is essential for building comparable history from OEWS vintages published before and after the 2018 taxonomy revision.

**Source URL:** `https://www.bls.gov/soc/2018/soc_2018_crosswalk.xlsx`

The crosswalk contains:

- `2010 SOC Code` + `2010 SOC Title`
- `2018 SOC Code` + `2018 SOC Title`

Mappings are many-to-many: a single 2010 code may map to multiple 2018 codes (splits) and multiple 2010 codes may map to a single 2018 code (merges).

### Data Model

**New bridge table:** `bridge_soc_crosswalk`:

```
bridge_soc_crosswalk
    crosswalk_key       INTEGER PRIMARY KEY
    source_soc_code     TEXT NOT NULL          -- 2010 SOC code
    source_soc_version  TEXT NOT NULL          -- '2010'
    target_soc_code     TEXT NOT NULL          -- 2018 SOC code
    target_soc_version  TEXT NOT NULL          -- '2018'
    mapping_type        TEXT NOT NULL          -- '1:1', 'split', 'merge', 'complex'
    source_release_id   TEXT NOT NULL
```

**Mapping type classification:**

- **1:1** — One 2010 code maps to exactly one 2018 code. Values can be directly compared.
- **Split** — One 2010 code maps to multiple 2018 codes. The 2010 value is an aggregate of the 2018 components. Comparable history requires summing 2018 values to match the 2010 definition.
- **Merge** — Multiple 2010 codes map to one 2018 code. The 2018 value is an aggregate of the 2010 components. Comparable history requires summing 2010 values.
- **Complex** — Mixed splits and merges. These are excluded from comparable history in the initial release.

### Pipeline

**Manifest:** Add entry for `soc_crosswalk` pointing to the BLS crosswalk XLSX.

**Parser:** New `parse_soc_crosswalk()` function in `src/jobclass/parse/soc.py`. Read the XLSX, extract code pairs, classify each mapping as 1:1, split, merge, or complex by counting the cardinality of each source and target code.

**Loader:** Load `bridge_soc_crosswalk` with idempotent delete-before-insert on `source_release_id`.

**Comparable history extension:** Modify `build_comparable_history()` in `timeseries_refresh.py`:

1. For **1:1 mappings**: OEWS vintages using SOC 2010 can be directly compared to SOC 2018 vintages by remapping the occupation_key through the crosswalk.
2. For **splits and merges**: Sum the component values when building comparable-history observations. Flag these as `mapping_type = 'aggregated'` for transparency.
3. For **complex mappings**: Exclude from comparable history. These occupations will only have as-published history within each SOC version.

**OEWS 2012–2017 manifest entries:** Add OEWS national and state URLs for vintages 2012 through 2017. The parsers already handle column variations across vintages.

### Crosswalk-Specific Considerations

- The crosswalk XLSX may have multiple sheets or non-standard headers. The parser must handle this.
- Some 2010 codes have no 2018 equivalent (discontinued occupations). These get no crosswalk entry.
- Employment values can be summed across splits/merges. Wage values (mean, median) cannot be meaningfully averaged without employment weights. The initial implementation should only build comparable wage history for 1:1 mappings. Employment counts can use all mapping types.
- The `dim_occupation` table currently only contains SOC 2018 occupations. SOC 2010 occupations should be loaded as additional rows with `soc_version = '2010'` and `is_current = false`.

---

## 11. Website Impact Summary

| Source | New API Endpoints | New Profile Sections | New Pages | Metric Dropdowns |
|--------|------------------|---------------------|-----------|-----------------|
| DS-01 Knowledge | `/occupations/{soc}/knowledge` | Knowledge | None | None |
| DS-02 Abilities | `/occupations/{soc}/abilities` | Abilities | None | None |
| DS-03 Work Activities | `/occupations/{soc}/activities` | Work Activities | None | None |
| DS-04 Education | `/occupations/{soc}/education` | Education & Training | None | None |
| DS-05 Technology | `/occupations/{soc}/technology` | Tools & Technology | None | None |
| DS-06 CPI | None (new metrics in existing endpoints) | None | None | Real Mean/Median Wage |
| DS-07 Crosswalk | None (extends existing time-series) | None | None | None (more historical data) |

## 12. Static Site Impact

Each new per-occupation endpoint (DS-01 through DS-05) requires:

1. A new JSON file per occupation in `build_static.py` (e.g., `api/occupations/{soc}/knowledge.json`)
2. The occupation profile JS already uses a hide-and-reveal pattern — new sections follow the same approach.

DS-06 (CPI) adds new metric options to existing dropdowns. The static site already generates per-metric trend files; the real wage metrics will be generated as additional files.

DS-07 (crosswalk) extends existing time-series data. No new static site structure needed, but the pre-generated trend JSON files will contain more years of data.

## 13. Testing Strategy

Each source follows the established three-directory test pattern:

- **`tests/unit/`** — Parser tests on representative sample files. Schema contract tests for new tables. Idempotency tests for loaders.
- **`tests/web/`** — API endpoint tests (200 status, expected fields, empty-data handling). Profile page tests (section visibility, correct rendering).
- **`tests/warehouse/`** — Real data validation. Row counts, referential integrity, grain uniqueness. Skipped automatically if warehouse.duckdb is absent.

CPI-specific tests: verify deflation formula produces known values for a test year.

Crosswalk-specific tests: verify mapping type classification (1:1, split, merge, complex) against known examples. Verify comparable history includes crosswalked observations.

## 14. Out of Scope

- Job posting data (Lightcast, Indeed) — requires commercial licensing and title-to-SOC mapping infrastructure.
- CPS microdata — monthly grain, complex survey methodology, different analytical patterns.
- JOLTS — industry-based, not occupation-based. Requires industry-to-occupation bridging not yet designed.
- QCEW — quarterly, county-level, industry-based. Very different grain from current warehouse.
- Census ACS — complex survey with different granularity. Useful but a separate project.
- ISCO international harmonization — explicitly deferred per base design document.
- Per-capita measures — requires population data integration beyond CPI.

## 15. Ordering and Dependencies

```
DS-01 (Knowledge) ──┐
DS-02 (Abilities) ──┤── No dependencies. Can start immediately.
DS-03 (Activities) ─┤   All use existing O*NET infrastructure.
DS-04 (Education) ──┤
DS-05 (Technology) ─┘

DS-06 (CPI) ──────────── No dependency on DS-01–05.
                          Requires dim_time_period (already exists).

DS-07 (Crosswalk) ─────── No dependency on DS-01–06.
                          Requires dim_occupation with SOC 2010 rows.
                          Requires additional OEWS vintages (2012–2017).
```

All seven sources can be developed independently. DS-01 and DS-02 require zero new downloads and are the fastest to ship. DS-06 and DS-07 have the highest analytical value.
