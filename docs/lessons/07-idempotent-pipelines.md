# Idempotent Pipeline Design

## The Lesson

Data pipelines fail — downloads timeout, parsers hit unexpected formats, database connections drop. Idempotency (running the same operation twice produces the same result as running it once) must be designed into every layer: delete-before-insert for facts, check-before-insert for dimensions, and grain uniqueness constraints as the final safety net.

## Context

The JobClass pipeline downloads, parses, validates, and loads federal labor data from multiple sources into a DuckDB warehouse. Each run processes multiple datasets, any of which can fail independently. A partial failure followed by a restart must not create duplicate rows, corrupt dimension keys, or lose data that was successfully loaded before the failure.

## What Happened

1. **Fact tables were loaded with delete-before-insert at release grain.** The OEWS loader deletes all existing rows for a given `source_release_id` before inserting new ones. If the pipeline crashes after the delete but before the insert, the next run deletes nothing (already gone) and inserts fresh. If it crashes after both steps, the next run deletes the partial data and re-inserts completely. Either way, no duplicates:

   ```sql
   -- 1. Delete any existing rows for this release
   DELETE FROM stage__bls__oews_national WHERE source_release_id = ?

   -- 2. Insert the new rows
   INSERT INTO stage__bls__oews_national (...) VALUES (...)
   ```

2. **Dimension tables were loaded with check-before-insert on business key.** Dimensions grow over time (new geographies, new occupations) but existing rows are never duplicated or modified. The loader checks for the business key before inserting:

   ```sql
   INSERT INTO dim_geography (geo_type, geo_code, geo_name, ...)
   SELECT ?, ?, ?, ...
   WHERE NOT EXISTS (
       SELECT 1 FROM dim_geography WHERE geo_type = ? AND geo_code = ?
   )
   ```

3. **Grain uniqueness constraints were added as the final safety net.** The fact table's unique constraint on its grain columns rejects duplicates at the database level, catching any loader bug that the delete-before-insert pattern missed:

   ```sql
   UNIQUE (reference_period, geography_key, industry_key, ownership_code,
           occupation_key, source_dataset)
   ```

4. **Idempotence tests were added to every test suite.** Each test loads data, records the row count, loads again with the same input, and verifies the count hasn't changed. This catches regressions in idempotency logic that unit tests of individual SQL statements would miss.

## Key Insights

- **Delete-before-insert is simpler and safer than upsert for fact tables.** An upsert (`INSERT ... ON CONFLICT UPDATE`) requires defining what "update" means for every column. Delete-before-insert at release grain is unambiguous: the entire release is replaced atomically. The only risk is a crash between delete and insert, which the next run self-heals.
- **Dimension idempotency is check-before-insert, not delete-before-insert.** Deleting dimension rows would invalidate foreign keys in fact tables. Dimensions must only grow, never shrink. The `WHERE NOT EXISTS` pattern ensures this.
- **The database constraint is the final safety net, not the primary defense.** The grain uniqueness constraint catches bugs in loader logic — it should never fire during normal operation. If it fires, the loader has a bug. But having it means the bug produces an error instead of silent corruption.
- **Idempotence tests are integration tests, not unit tests.** Testing that "load twice, count once" works requires running the full loader against a real (or in-memory) database. Mocking the database away defeats the purpose — the idempotency guarantee lives in the SQL, not in the Python.

## Related Lessons

- [Dimensional Modeling for Labor Data](03-dimensional-modeling.md) — the schema design that idempotent loading maintains
- [Data Quality Traps in Government Sources](05-data-quality-traps.md) — the failure modes that make idempotency necessary
- [Testing and Deployment](09-testing-deployment.md) — the test suite that verifies idempotency
