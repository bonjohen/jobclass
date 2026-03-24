"""Time-series pipeline orchestration.

Orchestrates: dim_metric -> dim_time_period -> normalize observations ->
build comparable history -> compute derived series.
"""

from __future__ import annotations

import time

import duckdb

from jobclass.load.timeseries import (
    build_comparable_history,
    compute_rank_delta,
    compute_rolling_avg_3yr,
    compute_state_vs_national_gap,
    compute_yoy_absolute_change,
    compute_yoy_percent_change,
    normalize_oews_observations,
    normalize_projection_observations,
    populate_derived_metrics,
    populate_dim_metric,
    populate_dim_time_period,
)
from jobclass.observe.logging import get_logger
from jobclass.observe.run_manifest import generate_run_id

logger = get_logger(__name__)


def timeseries_refresh(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Execute the full time-series pipeline.

    Returns a dict of step names to row counts.
    """
    run_id = generate_run_id()
    results: dict[str, int] = {}

    steps = [
        ("populate_dim_metric", lambda: populate_dim_metric(conn)),
        ("populate_derived_metrics", lambda: populate_derived_metrics(conn)),
        ("populate_dim_time_period", lambda: populate_dim_time_period(conn)),
        (
            "normalize_oews_observations",
            lambda: normalize_oews_observations(conn, "as_published", run_id),
        ),
        (
            "normalize_projection_observations",
            lambda: normalize_projection_observations(conn, "as_published", run_id),
        ),
        ("build_comparable_history", lambda: build_comparable_history(conn)),
        ("compute_yoy_absolute_change", lambda: compute_yoy_absolute_change(conn, run_id)),
        ("compute_yoy_percent_change", lambda: compute_yoy_percent_change(conn, run_id)),
        ("compute_rolling_avg_3yr", lambda: compute_rolling_avg_3yr(conn, run_id)),
        (
            "compute_state_vs_national_gap",
            lambda: compute_state_vs_national_gap(conn, run_id),
        ),
        ("compute_rank_delta", lambda: compute_rank_delta(conn, run_id)),
    ]

    for step_name, step_fn in steps:
        t0 = time.time()
        try:
            count = step_fn()
            elapsed = time.time() - t0
            results[step_name] = count
            logger.info("  %s: %d rows (%.1fs)", step_name, count, elapsed)
        except Exception as e:
            elapsed = time.time() - t0
            logger.error("  %s: FAILED after %.1fs — %s", step_name, elapsed, e)
            # Partial failure: base observations remain intact
            results[step_name] = -1
            if step_name.startswith(("populate_", "normalize_")):
                raise  # Critical steps must not fail silently

    return results
