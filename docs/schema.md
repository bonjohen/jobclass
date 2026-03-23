# Warehouse Schema Documentation

## Layer Overview

| Layer | Prefix | Purpose |
|-------|--------|---------|
| Raw | `raw/` (filesystem) | Immutable source file capture |
| Staging | `stage__` | Parsed, typed, standardized rows |
| Core | `dim_`, `fact_`, `bridge_` | Conformed dimensions, facts, bridges |
| Marts | Views | Analyst-ready denormalized output |

## Staging Tables

### stage__soc__hierarchy
SOC taxonomy hierarchy parsed from BLS structure file.

| Column | Type | Description |
|--------|------|-------------|
| soc_code | TEXT | Standard Occupational Classification code |
| occupation_title | TEXT | Occupation title |
| occupation_level | INTEGER | Hierarchy level (1=major, 2=minor, 3=broad, 4=detailed) |
| occupation_level_name | TEXT | Level name |
| parent_soc_code | TEXT | Parent code in hierarchy |
| source_release_id | TEXT | SOC version year |
| parser_version | TEXT | Parser version that produced row |

### stage__soc__definitions
SOC occupation definitions.

| Column | Type | Description |
|--------|------|-------------|
| soc_code | TEXT | SOC code |
| occupation_definition | TEXT | Full definition text |
| source_release_id | TEXT | SOC version year |
| parser_version | TEXT | Parser version |

### stage__bls__oews_national / stage__bls__oews_state
OEWS employment and wage estimates. Same schema for national and state.

| Column | Type | Description |
|--------|------|-------------|
| area_type | TEXT | Geography type (national, state) |
| area_code | TEXT | BLS area code |
| area_title | TEXT | Area name |
| naics_code | TEXT | Industry code |
| naics_title | TEXT | Industry name |
| ownership_code | TEXT | Ownership type |
| occupation_code | TEXT | SOC code |
| occupation_title | TEXT | Occupation name |
| occupation_group | TEXT | Level indicator |
| employment_count | INTEGER | Employment estimate |
| employment_rse | DOUBLE | Relative standard error |
| jobs_per_1000 | DOUBLE | Jobs per 1,000 total employment |
| location_quotient | DOUBLE | Location quotient |
| mean_hourly_wage | DOUBLE | Mean hourly wage |
| mean_annual_wage | DOUBLE | Mean annual wage |
| mean_wage_rse | DOUBLE | Mean wage RSE |
| median_hourly_wage | DOUBLE | Median hourly wage |
| median_annual_wage | DOUBLE | Median annual wage |
| p10–p90_hourly_wage | DOUBLE | Percentile wages (10th, 25th, 75th, 90th) |
| source_release_id | TEXT | OEWS release identifier |
| parser_version | TEXT | Parser version |

### stage__onet__skills / stage__onet__knowledge / stage__onet__abilities
O*NET descriptor staging. Same schema across all three domains.

| Column | Type | Description |
|--------|------|-------------|
| occupation_code | TEXT | SOC code (O*NET suffix stripped) |
| element_id | TEXT | Descriptor element ID |
| element_name | TEXT | Descriptor name |
| scale_id | TEXT | Scale identifier (IM=importance, LV=level) |
| data_value | DOUBLE | Score value |
| n | INTEGER | Sample size |
| standard_error | DOUBLE | Standard error |
| lower_ci / upper_ci | DOUBLE | Confidence interval bounds |
| recommend_suppress | BOOLEAN | Suppression flag |
| not_relevant | BOOLEAN | Not-relevant flag |
| date | TEXT | Data collection date |
| domain_source | TEXT | Source domain |
| source_release_id | TEXT | O*NET release version |
| parser_version | TEXT | Parser version |

### stage__onet__tasks
O*NET task statements.

| Column | Type | Description |
|--------|------|-------------|
| occupation_code | TEXT | SOC code |
| task_id | TEXT | Task identifier |
| task | TEXT | Task description |
| task_type | TEXT | Task type |
| incumbents_responding | INTEGER | Survey respondent count |
| date | TEXT | Collection date |
| domain_source | TEXT | Source domain |
| source_release_id | TEXT | O*NET release version |
| parser_version | TEXT | Parser version |

### stage__bls__employment_projections
BLS employment projections.

| Column | Type | Description |
|--------|------|-------------|
| projection_cycle | TEXT | Projection period (e.g. "2022-2032") |
| occupation_code | TEXT | SOC code |
| occupation_title | TEXT | Occupation name |
| base_year | INTEGER | Projection base year |
| projection_year | INTEGER | Target projection year |
| employment_base | INTEGER | Employment at base year |
| employment_projected | INTEGER | Projected employment |
| employment_change_abs | INTEGER | Absolute change |
| employment_change_pct | DOUBLE | Percentage change |
| annual_openings | INTEGER | Annual job openings |
| education_category | TEXT | Typical education requirement |
| training_category | TEXT | Training category |
| work_experience_category | TEXT | Work experience requirement |
| source_release_id | TEXT | Release identifier |
| parser_version | TEXT | Parser version |

## Core Dimensions

### dim_occupation
Conformed occupation dimension with hierarchy fields.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| occupation_key | INTEGER | PK | Surrogate key |
| soc_code | TEXT | BK | SOC code |
| occupation_title | TEXT | | Title |
| occupation_level | INTEGER | | Hierarchy level |
| occupation_level_name | TEXT | | Level name |
| parent_soc_code | TEXT | | Parent in hierarchy |
| major_group_code | TEXT | | Major group (XX-0000) |
| minor_group_code | TEXT | | Minor group (XX-YZ00) |
| broad_occupation_code | TEXT | | Broad occupation (XX-YZW0) |
| detailed_occupation_code | TEXT | | Detailed code |
| occupation_definition | TEXT | | Full text definition |
| soc_version | TEXT | BK | SOC version year |
| is_leaf | BOOLEAN | | True if detailed occupation |
| is_current | BOOLEAN | | True if active version |
| source_release_id | TEXT | | Source lineage |

### dim_geography
Geography dimension for OEWS area codes.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| geography_key | INTEGER | PK | Surrogate key |
| geo_type | TEXT | BK | national, state, msa |
| geo_code | TEXT | BK | BLS area code |
| geo_name | TEXT | | Area name |
| state_fips | TEXT | | State FIPS code |
| is_current | BOOLEAN | | Active flag |
| source_release_id | TEXT | BK | Release lineage |

### dim_industry
Industry dimension (NAICS).

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| industry_key | INTEGER | PK | Surrogate key |
| naics_code | TEXT | BK | NAICS code |
| industry_title | TEXT | | Industry name |
| naics_version | TEXT | BK | NAICS version |
| is_current | BOOLEAN | | Active flag |

### dim_skill / dim_knowledge / dim_ability
O*NET descriptor dimensions. Same structure for all three.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| {domain}_key | INTEGER | PK | Surrogate key |
| element_id | TEXT | BK | O*NET element ID |
| element_name | TEXT | | Descriptor name |
| source_version | TEXT | BK | O*NET version |
| is_current | BOOLEAN | | Active flag |

### dim_task
O*NET task dimension.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| task_key | INTEGER | PK | Surrogate key |
| task_id | TEXT | BK | Task identifier |
| task | TEXT | | Task description |
| task_type | TEXT | | Task type |
| source_version | TEXT | BK | O*NET version |
| is_current | BOOLEAN | | Active flag |

## Core Facts

### fact_occupation_employment_wages
OEWS employment and wage measures.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| fact_id | INTEGER | PK | Surrogate key |
| reference_period | TEXT | | Business reference period |
| estimate_year | INTEGER | | Estimate year |
| geography_key | INTEGER | FK | → dim_geography |
| industry_key | INTEGER | FK | → dim_industry |
| ownership_code | TEXT | | Ownership type |
| occupation_key | INTEGER | FK | → dim_occupation |
| employment_count | INTEGER | | Employment estimate |
| mean_hourly_wage | DOUBLE | | Mean hourly wage |
| mean_annual_wage | DOUBLE | | Mean annual wage |
| median_hourly_wage | DOUBLE | | Median hourly wage |
| median_annual_wage | DOUBLE | | Median annual wage |
| p10–p90_hourly_wage | DOUBLE | | Wage percentiles |
| source_dataset | TEXT | | oews_national or oews_state |
| source_release_id | TEXT | | Release lineage |

### fact_occupation_projections
BLS employment projections.

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| fact_id | INTEGER | PK | Surrogate key |
| projection_cycle | TEXT | BK | e.g. "2022-2032" |
| occupation_key | INTEGER | FK/BK | → dim_occupation |
| base_year | INTEGER | | Projection base year |
| projection_year | INTEGER | | Target year |
| employment_base | INTEGER | | Base employment |
| employment_projected | INTEGER | | Projected employment |
| employment_change_abs | INTEGER | | Absolute change |
| employment_change_pct | DOUBLE | | Percentage change |
| annual_openings | INTEGER | | Annual openings |
| education_category | TEXT | | Typical education |
| source_release_id | TEXT | | Release lineage |

## Bridge Tables

### bridge_occupation_hierarchy
Parent-child occupation relationships.

| Column | Type | Description |
|--------|------|-------------|
| parent_occupation_key | INTEGER | → dim_occupation |
| child_occupation_key | INTEGER | → dim_occupation |
| relationship_level | INTEGER | Levels between parent and child |
| soc_version | TEXT | SOC version |
| source_release_id | TEXT | Release lineage |

### bridge_occupation_skill / knowledge / ability
Occupation-to-descriptor bridges. Same pattern for all three.

| Column | Type | Description |
|--------|------|-------------|
| occupation_key | INTEGER | → dim_occupation |
| {domain}_key | INTEGER | → dim_{domain} |
| scale_id | TEXT | IM or LV |
| data_value | DOUBLE | Score |
| n | INTEGER | Sample size |
| source_version | TEXT | O*NET version |
| source_release_id | TEXT | Release lineage |

### bridge_occupation_task
Occupation-to-task bridge.

| Column | Type | Description |
|--------|------|-------------|
| occupation_key | INTEGER | → dim_occupation |
| task_key | INTEGER | → dim_task |
| data_value | DOUBLE | Score |
| n | INTEGER | Sample size |
| source_version | TEXT | O*NET version |
| source_release_id | TEXT | Release lineage |

## Mart Views

| View | Grain | Purpose |
|------|-------|---------|
| occupation_summary | One row per current occupation | Hierarchy fields, definition, SOC version |
| occupation_wages_by_geography | occupation × geography | Employment counts and wage distribution |
| occupation_skill_profile | occupation × skill × scale | Skill scores from current O*NET |
| occupation_task_profile | occupation × task | Task descriptions from current O*NET |
| occupation_similarity_seeded | occupation pair | Jaccard similarity based on shared skills |
