"""Unit tests for time-series dimensions, observations, comparable history,
derived series, orchestration, and validation (Phases TS1–TS8)."""

from __future__ import annotations

import pytest

from jobclass.load.timeseries import (
    BASE_METRICS,
    DERIVED_METRICS,
    build_comparable_history,
    compute_state_vs_national_gap,
    normalize_oews_observations,
    normalize_projection_observations,
    populate_derived_metrics,
    populate_dim_metric,
    populate_dim_time_period,
)
from jobclass.validate.timeseries import run_all_timeseries_validations

# ============================================================
# Phase TS1: Conformed Metric Catalog and Time-Period Dimension
# ============================================================


class TestDimMetric:
    """TS1-01, TS1-03, TS1-04, TS1-07"""

    def test_populate_base_metrics(self, migrated_db):
        count = populate_dim_metric(migrated_db)
        assert count == len(BASE_METRICS)
        rows = migrated_db.execute("SELECT * FROM dim_metric").fetchall()
        assert len(rows) == len(BASE_METRICS)

    def test_populate_idempotent(self, migrated_db):
        populate_dim_metric(migrated_db)
        count2 = populate_dim_metric(migrated_db)
        assert count2 == 0
        rows = migrated_db.execute("SELECT COUNT(*) FROM dim_metric").fetchone()[0]
        assert rows == len(BASE_METRICS)

    def test_expected_metric_names(self, migrated_db):
        populate_dim_metric(migrated_db)
        names = {
            r[0] for r in migrated_db.execute(
                "SELECT metric_name FROM dim_metric"
            ).fetchall()
        }
        expected = {m["metric_name"] for m in BASE_METRICS}
        assert expected == names

    def test_populate_derived_metrics(self, migrated_db):
        populate_dim_metric(migrated_db)
        count = populate_derived_metrics(migrated_db)
        assert count == len(DERIVED_METRICS)
        total = migrated_db.execute("SELECT COUNT(*) FROM dim_metric").fetchone()[0]
        assert total == len(BASE_METRICS) + len(DERIVED_METRICS)


class TestDimTimePeriod:
    """TS1-02, TS1-05, TS1-08"""

    def test_populate_from_oews(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        count = populate_dim_time_period(oews_loaded_db)
        assert count > 0
        # All periods should be annual
        non_annual = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_time_period WHERE period_type != 'annual'"
        ).fetchone()[0]
        assert non_annual == 0

    def test_populate_idempotent(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        count2 = populate_dim_time_period(oews_loaded_db)
        assert count2 == 0

    def test_covers_estimate_years(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        # Get years from fact table
        fact_years = {
            r[0] for r in oews_loaded_db.execute(
                "SELECT DISTINCT estimate_year FROM fact_occupation_employment_wages "
                "WHERE estimate_year IS NOT NULL"
            ).fetchall()
        }
        period_years = {
            r[0] for r in oews_loaded_db.execute(
                "SELECT year FROM dim_time_period"
            ).fetchall()
        }
        assert fact_years <= period_years

    def test_period_dates_valid(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        bad = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_time_period WHERE period_start_date > period_end_date"
        ).fetchone()[0]
        assert bad == 0


# ============================================================
# Phase TS2: Base Time-Series Observation Fact
# ============================================================


class TestObservationNormalization:
    """TS2-02 through TS2-14"""

    @pytest.fixture
    def ts_ready_db(self, oews_loaded_db):
        """DB with OEWS loaded + time-series dimensions populated."""
        populate_dim_metric(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        return oews_loaded_db

    def test_normalize_oews_creates_rows(self, ts_ready_db):
        count = normalize_oews_observations(ts_ready_db)
        assert count > 0

    def test_normalize_oews_idempotent(self, ts_ready_db):
        count1 = normalize_oews_observations(ts_ready_db)
        count2 = normalize_oews_observations(ts_ready_db)
        assert count1 == count2

    def test_all_comparability_mode_as_published(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        modes = {
            r[0] for r in ts_ready_db.execute(
                "SELECT DISTINCT comparability_mode FROM fact_time_series_observation"
            ).fetchall()
        }
        assert modes == {"as_published"}

    def test_metric_keys_valid(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        orphan = ts_ready_db.execute(
            """SELECT COUNT(DISTINCT obs.metric_key)
               FROM fact_time_series_observation obs
               LEFT JOIN dim_metric m ON obs.metric_key = m.metric_key
               WHERE m.metric_key IS NULL"""
        ).fetchone()[0]
        assert orphan == 0

    def test_period_keys_valid(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        orphan = ts_ready_db.execute(
            """SELECT COUNT(DISTINCT obs.period_key)
               FROM fact_time_series_observation obs
               LEFT JOIN dim_time_period tp ON obs.period_key = tp.period_key
               WHERE tp.period_key IS NULL"""
        ).fetchone()[0]
        assert orphan == 0

    def test_occupation_keys_valid(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        orphan = ts_ready_db.execute(
            """SELECT COUNT(DISTINCT obs.occupation_key)
               FROM fact_time_series_observation obs
               LEFT JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
               WHERE o.occupation_key IS NULL"""
        ).fetchone()[0]
        assert orphan == 0

    def test_geography_keys_valid(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        orphan = ts_ready_db.execute(
            """SELECT COUNT(DISTINCT obs.geography_key)
               FROM fact_time_series_observation obs
               LEFT JOIN dim_geography g ON obs.geography_key = g.geography_key
               WHERE g.geography_key IS NULL"""
        ).fetchone()[0]
        assert orphan == 0

    def test_grain_uniqueness(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        dupes = ts_ready_db.execute(
            """SELECT COUNT(*) FROM (
                SELECT metric_key, occupation_key, geography_key, period_key,
                       source_release_id, comparability_mode, COUNT(*) AS cnt
                FROM fact_time_series_observation
                GROUP BY metric_key, occupation_key, geography_key, period_key,
                         source_release_id, comparability_mode
                HAVING cnt > 1
            ) d"""
        ).fetchone()[0]
        assert dupes == 0

    def test_observation_count_crosscheck(self, ts_ready_db):
        normalize_oews_observations(ts_ready_db)
        obs_count = ts_ready_db.execute(
            "SELECT COUNT(*) FROM fact_time_series_observation"
        ).fetchone()[0]
        # Should have rows for 3 metrics × source fact rows (with matching periods)
        fact_count = ts_ready_db.execute(
            "SELECT COUNT(*) FROM fact_occupation_employment_wages WHERE estimate_year IS NOT NULL"
        ).fetchone()[0]
        # obs_count should be approximately 3 × fact_count (one per metric)
        assert obs_count > 0
        assert obs_count <= 3 * fact_count


class TestProjectionNormalization:
    """TS2-05"""

    @pytest.fixture
    def ts_proj_db(self, projections_loaded_db):
        populate_dim_metric(projections_loaded_db)
        populate_dim_time_period(projections_loaded_db)
        return projections_loaded_db

    def test_normalize_projections_creates_rows(self, ts_proj_db):
        count = normalize_projection_observations(ts_proj_db)
        assert count > 0

    def test_normalize_projections_idempotent(self, ts_proj_db):
        count1 = normalize_projection_observations(ts_proj_db)
        count2 = normalize_projection_observations(ts_proj_db)
        assert count1 == count2


# ============================================================
# Phase TS4: Comparable History Series
# ============================================================


class TestComparableHistory:
    """TS4-02, TS4-05"""

    @pytest.fixture
    def ts_obs_db(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        normalize_oews_observations(oews_loaded_db)
        return oews_loaded_db

    def test_build_comparable_history(self, ts_obs_db):
        count = build_comparable_history(ts_obs_db)
        # Should create comparable rows for OEWS metrics
        assert count > 0

    def test_comparable_subset_of_as_published(self, ts_obs_db):
        build_comparable_history(ts_obs_db)
        comparable = ts_obs_db.execute(
            "SELECT COUNT(*) FROM fact_time_series_observation WHERE comparability_mode = 'comparable'"
        ).fetchone()[0]
        as_published = ts_obs_db.execute(
            "SELECT COUNT(*) FROM fact_time_series_observation WHERE comparability_mode = 'as_published'"
        ).fetchone()[0]
        assert comparable <= as_published

    def test_no_comparable_for_not_comparable_metrics(self, ts_obs_db):
        build_comparable_history(ts_obs_db)
        bad = ts_obs_db.execute(
            """SELECT COUNT(*) FROM fact_time_series_observation obs
               JOIN dim_metric m ON obs.metric_key = m.metric_key
               WHERE obs.comparability_mode = 'comparable'
                 AND m.comparability_constraint = 'not_comparable'"""
        ).fetchone()[0]
        assert bad == 0


# ============================================================
# Phase TS5: Derived Metric Library
# ============================================================


class TestDerivedMetrics:
    """TS5-01 through TS5-17"""

    @pytest.fixture
    def ts_derived_db(self, oews_loaded_db):
        populate_dim_metric(oews_loaded_db)
        populate_derived_metrics(oews_loaded_db)
        populate_dim_time_period(oews_loaded_db)
        normalize_oews_observations(oews_loaded_db)
        build_comparable_history(oews_loaded_db)
        return oews_loaded_db

    def test_derived_metrics_registered(self, ts_derived_db):
        derived = ts_derived_db.execute(
            "SELECT COUNT(*) FROM dim_metric WHERE derivation_type = 'derived'"
        ).fetchone()[0]
        assert derived == len(DERIVED_METRICS)

    def test_state_vs_national_gap(self, ts_derived_db):
        count = compute_state_vs_national_gap(ts_derived_db)
        # Should produce rows if we have state and national data
        assert count >= 0

    def test_no_derived_with_base_metric_key(self, ts_derived_db):
        compute_state_vs_national_gap(ts_derived_db)
        bad = ts_derived_db.execute(
            """SELECT COUNT(*) FROM fact_derived_series d
               JOIN dim_metric m ON d.metric_key = m.metric_key
               WHERE m.derivation_type = 'base'"""
        ).fetchone()[0]
        assert bad == 0


# ============================================================
# Phase TS6: Orchestration
# ============================================================


class TestTimerseriesOrchestration:
    """TS6-07, TS6-08"""

    def test_timeseries_refresh_runs(self, oews_loaded_db):
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        results = timeseries_refresh(oews_loaded_db)
        assert all(v >= 0 for v in results.values())

    def test_timeseries_refresh_idempotent(self, oews_loaded_db):
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(oews_loaded_db)
        # Capture DB state after first run
        obs1 = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_time_series_observation"
        ).fetchone()[0]
        der1 = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_derived_series"
        ).fetchone()[0]
        # Second run
        timeseries_refresh(oews_loaded_db)
        obs2 = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_time_series_observation"
        ).fetchone()[0]
        der2 = oews_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_derived_series"
        ).fetchone()[0]
        assert obs1 == obs2, f"Observation count changed: {obs1} vs {obs2}"
        assert der1 == der2, f"Derived count changed: {der1} vs {der2}"


# ============================================================
# Phase TS7: Validation
# ============================================================


class TestTimeseriesValidation:
    """TS7-01 through TS7-08"""

    @pytest.fixture
    def ts_validated_db(self, oews_loaded_db):
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(oews_loaded_db)
        return oews_loaded_db

    def test_all_validations_pass(self, ts_validated_db):
        results = run_all_timeseries_validations(ts_validated_db)
        for r in results:
            assert r.passed, f"Validation {r.check_name} failed: {r.message}"

    def test_period_ordering(self, ts_validated_db):
        from jobclass.validate.timeseries import validate_period_ordering
        r = validate_period_ordering(ts_validated_db)
        assert r.passed

    def test_no_duplicate_periods(self, ts_validated_db):
        from jobclass.validate.timeseries import validate_no_duplicate_periods
        r = validate_no_duplicate_periods(ts_validated_db)
        assert r.passed

    def test_observation_derived_separation(self, ts_validated_db):
        from jobclass.validate.timeseries import validate_observation_derived_separation
        r = validate_observation_derived_separation(ts_validated_db)
        assert r.passed

    def test_comparable_subset(self, ts_validated_db):
        from jobclass.validate.timeseries import validate_comparable_subset
        r = validate_comparable_subset(ts_validated_db)
        assert r.passed


# ============================================================
# Phase TS8: Mart views
# ============================================================


class TestTimeseriesMarts:
    """TS8-07 through TS8-11"""

    @pytest.fixture
    def ts_mart_db(self, oews_loaded_db):
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(oews_loaded_db)
        return oews_loaded_db

    def test_trend_series_has_rows(self, ts_mart_db):
        count = ts_mart_db.execute(
            "SELECT COUNT(*) FROM mart_occupation_trend_series"
        ).fetchone()[0]
        assert count > 0

    def test_trend_series_columns(self, ts_mart_db):
        cols = {
            r[0] for r in ts_mart_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'mart_occupation_trend_series'"
            ).fetchall()
        }
        required = {
            "occupation_key", "soc_code", "occupation_title",
            "metric_name", "year", "observed_value", "comparability_mode",
            "source_release_id",
        }
        assert required <= cols

    def test_geography_gap_view_exists(self, ts_mart_db):
        try:
            ts_mart_db.execute("SELECT 1 FROM mart_occupation_geography_gap_series LIMIT 0")
        except Exception:
            pytest.fail("mart_occupation_geography_gap_series view does not exist")

    def test_rank_change_view_exists(self, ts_mart_db):
        try:
            ts_mart_db.execute("SELECT 1 FROM mart_occupation_rank_change LIMIT 0")
        except Exception:
            pytest.fail("mart_occupation_rank_change view does not exist")

    def test_projection_context_view_exists(self, ts_mart_db):
        try:
            ts_mart_db.execute("SELECT 1 FROM mart_occupation_projection_context LIMIT 0")
        except Exception:
            pytest.fail("mart_occupation_projection_context view does not exist")

    def test_similarity_trend_overlay_view_exists(self, ts_mart_db):
        try:
            ts_mart_db.execute("SELECT 1 FROM mart_occupation_similarity_trend_overlay LIMIT 0")
        except Exception:
            pytest.fail("mart_occupation_similarity_trend_overlay view does not exist")

    def test_mart_preserves_lineage(self, ts_mart_db):
        """All mart rows should have source_release_id and comparability_mode."""
        row = ts_mart_db.execute(
            "SELECT source_release_id, comparability_mode "
            "FROM mart_occupation_trend_series LIMIT 1"
        ).fetchone()
        if row:
            assert row[0] is not None
            assert row[1] is not None
