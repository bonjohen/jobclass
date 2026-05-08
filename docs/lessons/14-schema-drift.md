# Schema Drift Detection

## The Lesson

Government data sources change column names, add or remove columns, and retype columns between releases — often without notice. A pipeline that assumes a fixed schema will silently break or load garbage. Proactive drift detection at the staging boundary turns silent corruption into a loud, actionable failure at the earliest possible point.

## Context

A labor market data pipeline ingested data from BLS, O*NET, and SOC — all federal sources that publish periodic data releases with no formal schema contract. A renamed column would become all NULLs; a retyped column would truncate values or throw cast errors deep in the warehouse layer where the root cause was hard to trace. The pipeline needed a detection system that would catch these changes before they reached the warehouse.

## What Happened

1. **A schema comparison function was built.** The core detection compares two schema snapshots — each a `dict[str, str]` mapping column name to data type — and returns a list of `SchemaChange` objects classified as "added", "removed", or "retyped":

   ```python
   def detect_schema_drift(schema_a, schema_b):
       changes = []
       all_cols = set(schema_a.keys()) | set(schema_b.keys())
       for col in sorted(all_cols):
           if col in schema_a and col not in schema_b:
               changes.append(SchemaChange("removed", col))
           elif col not in schema_a and col in schema_b:
               changes.append(SchemaChange("added", col))
           elif schema_a[col].upper() != schema_b[col].upper():
               changes.append(SchemaChange("retyped", col))
       return changes
   ```

   The comparison is case-insensitive on type names because some sources report `VARCHAR` while the staging layer normalizes to `varchar`.

2. **Row count shift detection was added.** A 20% threshold catches major structural changes — such as BLS adding a new geography level or dropping an occupation group — while ignoring normal year-to-year variation:

   ```python
   ROW_COUNT_SHIFT_THRESHOLD_PCT = 20.0

   def detect_row_count_shift(prior_count, current_count, threshold_pct=20.0):
       pct_change = abs(current_count - prior_count) / prior_count * 100
       return ValidationResult(
           passed=pct_change < threshold_pct,
           message=f"Row count changed {pct_change:.1f}%"
       )
   ```

3. **Measure delta detection was layered on.** Beyond row counts, the pipeline checks for large relative changes in key measures (15% threshold), catching wage corrections and employment revisions that do not affect the schema or row count but would produce misleading trend analysis.

   | Check | Threshold | Catches |
   |---|---|---|
   | Row count shift | 20% | New geography levels, dropped occupation groups |
   | Measure delta | 15% | Wage corrections, employment revisions |
   | Schema drift | Any change | Column renames, type changes, removed fields |

4. **A binary publication gate was implemented.** All validation checks feed into a single gate that decides whether data flows from staging into the warehouse — pass everything or block everything:

   ```python
   def check_publication_gate(validation_results):
       failures = [r for r in validation_results if not r.passed]
       if failures:
           return f"BLOCKED: {len(failures)} validation(s) failed"
       return "ALLOWED: All validations passed"
   ```

   Raw data is always preserved regardless of gate outcome — the fix-and-re-run workflow never requires re-downloading.

## Key Insights

- **Fail fast at the boundary.** Schema drift caught at the staging layer is a clear, actionable error. The same drift caught in the warehouse layer is a mysterious data quality bug that requires forensic investigation.
- **The gate must be binary.** Partial publication (some tables pass, some fail) creates inconsistent warehouse state that is harder to debug than a full block. Either all validations pass or nothing flows.
- **Row count and measure deltas complement schema drift.** A source can change in volume or revise key values without altering its schema. The three checks together cover structural, volumetric, and value-level changes.
- **Raw immutability enables fix-and-re-run.** Because raw bytes are preserved regardless of validation outcome, a parser fix can be tested against the exact data that exposed the problem without waiting for a fresh download.

## Related Lessons

- [Data Quality Traps](05-data-quality-traps.md)
- [Idempotent Pipelines](07-idempotent-pipelines.md)
- [Government API Extract Patterns](17-government-apis.md)
