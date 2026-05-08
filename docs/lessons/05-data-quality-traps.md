# Data Quality Traps in Government Sources

## The Lesson

Government data sources contain artifacts of their internal production processes — temp files in archives, renamed columns between releases, duplicate hierarchical rows, suppressed values that look like nulls but carry legal meaning, and CDN configurations that reject non-browser HTTP clients. Defensive parsing must anticipate these traps because they will not be documented or fixed upstream.

## Context

The JobClass pipeline downloads and parses data from BLS (OEWS employment/wage surveys) and O*NET, published as ZIP-compressed Excel spreadsheets and CSVs. These sources are authoritative and well-structured at the schema level, but their packaging and formatting contain undocumented inconsistencies that cause silent data loss or loader failures if not anticipated.

## What Happened

1. **A temp file inside a ZIP archive broke the extractor.** The BLS OEWS 2022 state ZIP (`oesm22st.zip`) contained `~$state_M2022_dl.xlsx` — an Excel lock file left by whoever packaged the archive. The ZIP extractor selected it as the data file and failed with "File is not a zip file." The fix was filtering any filename starting with `~$` before selecting the XLSX:

   ```python
   xlsx_names = [
       n for n in zf.namelist()
       if n.lower().endswith(".xlsx") and not n.split("/")[-1].startswith("~$")
   ]
   ```

2. **Column names changed between vintages without notice.** OEWS 2023 uses `O_GROUP`, OEWS 2021 uses `OCC_GROUP`, and older files use `GROUP`. Similarly, `AREA_NAME` in one vintage becomes `AREA_TITLE` in another. An alias map in the parser normalizes all known variations to canonical names:

   ```python
   _OEWS_COLUMN_ALIASES = {
       "group": "o_group",
       "occ_group": "o_group",
       "area_name": "area_title",
       ...
   }
   ```

3. **Hierarchical group overlap created duplicate fact rows.** BLS reports both "broad" group `11-1010` and "detailed" occupation `11-1011` (Chief Executives) in OEWS data. Both carry identical employment and wage values. Loading both into the fact table and then normalizing into time-series observations violated the unique constraint on `(occupation_key, geography_key, period_key)`. The fix was `SELECT DISTINCT` during normalization — safe because the duplicate values are identical.

4. **Suppressed values were misinterpreted as missing data.** BLS suppresses wage and employment figures for confidentiality when respondent counts are too small. These arrive as null, `*`, or `**`. They mean "data exists but cannot be disclosed" — legally and semantically distinct from zero or absent. The rule was enforced through every layer: preserve nulls, never impute, display "Data suppressed" in the UI.

5. **BLS's CDN rejected programmatic downloads.** BLS.gov returns 403 Forbidden for HTTP requests missing browser-like headers. The downloader was updated to send `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, `Sec-Fetch-Site`, and `Sec-Fetch-User` headers. This is not scraping — the data is public — but the CDN enforces these checks regardless.

## Key Insights

- **Government publishers don't scrub their archives.** Temp files, lock files, and metadata artifacts end up in published ZIPs because the packaging process has no automated cleanup. Defensive extraction must filter known junk patterns before selecting the real data file.
- **Column aliases are a mandatory parser feature.** When a source renames columns between releases without a changelog, the parser must maintain a map of all known name variations. The first check when adding a new vintage should always be whether its column headers match the alias map.
- **Suppressed values are not nulls — they carry legal meaning.** BLS suppresses data for confidentiality. Imputing or zeroing these values violates the disclosure rules the suppression was designed to enforce. Every layer must propagate suppressed markers unchanged.
- **Deduplication before normalization prevents constraint violations.** When source data contains hierarchical overlaps (broad and detailed groups with identical values), `SELECT DISTINCT` at the normalization boundary is both safe and necessary.
- **Public data doesn't mean open access.** CDN-level request filtering on government sites requires browser-like headers even for legitimately public downloads. This is an infrastructure artifact, not a policy decision, but it still breaks naive HTTP clients.

## Related Lessons

- [Schema Drift Detection](14-schema-drift.md) — systematic handling of column and format changes across releases
- [The Multi-Vintage Challenge](04-multi-vintage-challenge.md) — the broader problem of loading multiple releases of the same dataset
- [Extract Patterns for Government APIs](17-government-apis.md) — patterns for working with government data distribution infrastructure
