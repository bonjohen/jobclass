# Thread-Safe Database Connections

## The Lesson

When a web framework dispatches synchronous endpoint handlers to a thread pool, a shared database connection will produce intermittent wrong results — not errors, but silently incorrect data. The fix is per-thread connections via `threading.local()`, with a global override path for test injection.

## Context

The JobClass web application uses FastAPI with synchronous endpoint handlers (`def`, not `async def`) that query a DuckDB warehouse. FastAPI dispatches sync handlers to a thread pool (default: 40 workers via `anyio`). The landing page fires multiple concurrent API requests (`/api/stats` and `/api/occupations/...`), each running on a different thread. The database layer initially shared a single DuckDB connection across all threads.

## What Happened

1. **Intermittent zeros appeared on the landing page.** The stats endpoint returned correct data when tested sequentially with `curl`, but in the browser, one or more stats occasionally showed `0` instead of the correct value. The bug was unreproducible on demand and never appeared in sequential testing.

2. **The concurrency pattern was identified.** FastAPI dispatches sync handlers (`def stats()`) to thread pool workers. When the browser fires two fetch requests simultaneously, they run on different threads. The key clue was that the bug only appeared in the browser (concurrent requests) and never in sequential `curl` calls.

3. **The shared connection was the root cause.** The database layer used a single global DuckDB connection:

   ```python
   # BROKEN: shared connection, no thread safety
   _conn = None

   def get_db():
       global _conn
       if _conn is not None:
           return _conn
       _conn = duckdb.connect("warehouse.duckdb", read_only=True)
       return _conn
   ```

   When two threads used this connection simultaneously, DuckDB's internal state could get corrupted — one thread's query might return empty results, partial results, or the wrong data entirely.

4. **Per-thread connections were implemented using `threading.local()`.** Each thread gets its own DuckDB connection that no other thread can access:

   ```python
   # FIXED: per-thread connections
   _local = threading.local()
   _test_conn = None

   def get_db():
       if _test_conn is not None:
           return _test_conn
       conn = getattr(_local, "conn", None)
       if conn is not None:
           return conn
       _local.conn = duckdb.connect(resolved_path, read_only=True)
       return _local.conn
   ```

5. **A test injection complication was resolved.** The test suite uses `set_db()` to inject a fixture connection from the main test thread. But `threading.local()` storage is invisible to other threads — FastAPI's worker threads wouldn't see the injected connection. The fix was a global `_test_conn` variable that takes priority over thread-local storage, visible to all threads.

## Key Insights

- **Shared connections produce wrong data, not errors.** The insidious aspect of this bug is that DuckDB doesn't raise an exception when two threads use the same connection. It silently returns incorrect results — zeros, partial data, or another query's results. Error-based debugging won't find it.
- **Intermittent bugs in web handlers point to concurrency.** When a bug appears in browser testing but not in sequential `curl` calls, the difference is concurrent requests. Browser pages that fire multiple `fetch()` calls on load are natural concurrency tests.
- **`threading.local()` is the standard Python solution for per-thread state.** It gives each thread its own attribute namespace. No locks, no pools, no connection management — each thread creates its connection on first use and reuses it thereafter.
- **Test injection must bypass thread-local storage.** A test fixture connection set on the main thread is invisible in `threading.local()` on worker threads. A global variable checked before thread-local lookup solves this without compromising thread safety in production.

### Framework Reference

| Framework | Sync Handler Dispatch | Needs Per-Thread DB? |
|-----------|----------------------|---------------------|
| FastAPI (sync def) | Thread pool | Yes |
| FastAPI (async def) | Event loop (single thread) | No |
| Flask (threaded=True) | Thread per request | Yes |
| Django (WSGI) | Thread per request | Yes |

## Related Lessons

- [Testing and Deployment](09-testing-deployment.md) — the test infrastructure where the fixture injection pattern is used
- [UI-Data Alignment](13-ui-data-alignment.md) — ensuring the data the UI receives matches what it expects
