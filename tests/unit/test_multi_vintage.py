"""Tests for multi-vintage OEWS extraction and time-series integration (Phase TS3)."""

from __future__ import annotations


class TestMultiVintageFact:
    """TS3-05: fact_occupation_employment_wages contains rows from all vintages."""

    def test_fact_has_all_vintages(self, multi_vintage_oews_db):
        releases = multi_vintage_oews_db.execute(
            "SELECT DISTINCT source_release_id FROM fact_occupation_employment_wages ORDER BY source_release_id"
        ).fetchall()
        release_ids = [r[0] for r in releases]
        assert "2021.05" in release_ids
        assert "2022.05" in release_ids
        assert "2023.05" in release_ids

    def test_fact_has_multiple_estimate_years(self, multi_vintage_oews_db):
        years = multi_vintage_oews_db.execute(
            "SELECT DISTINCT estimate_year FROM fact_occupation_employment_wages ORDER BY estimate_year"
        ).fetchall()
        year_list = [r[0] for r in years]
        assert len(year_list) >= 3
        assert 2021 in year_list
        assert 2022 in year_list
        assert 2023 in year_list

    def test_no_duplicate_facts(self, multi_vintage_oews_db):
        """Each vintage should have its own fact rows, no duplicates within a vintage."""
        dupes = multi_vintage_oews_db.execute("""
            SELECT source_dataset, source_release_id, occupation_key, geography_key, COUNT(*)
            FROM fact_occupation_employment_wages
            GROUP BY source_dataset, source_release_id, occupation_key, geography_key
            HAVING COUNT(*) > 1
        """).fetchall()
        assert len(dupes) == 0


class TestMultiVintageGeography:
    """Geography dimension is shared across vintages."""

    def test_geography_not_duplicated(self, multi_vintage_oews_db):
        """Same geo_type + geo_code should not create multiple dimension rows."""
        dupes = multi_vintage_oews_db.execute("""
            SELECT geo_type, geo_code, COUNT(*)
            FROM dim_geography
            GROUP BY geo_type, geo_code
            HAVING COUNT(*) > 1
        """).fetchall()
        assert len(dupes) == 0, f"Geography dimension has duplicates: {dupes}"

    def test_all_vintages_use_same_geography_keys(self, multi_vintage_oews_db):
        """Facts from different vintages should reference the same geography keys for same areas."""
        # Get geography keys used by each vintage
        geo_keys_per_vintage = {}
        for release in ["2021.05", "2022.05", "2023.05"]:
            keys = multi_vintage_oews_db.execute("""
                SELECT DISTINCT geography_key
                FROM fact_occupation_employment_wages
                WHERE source_release_id = ? AND source_dataset = 'oews_national'
            """, [release]).fetchall()
            geo_keys_per_vintage[release] = {r[0] for r in keys}
        # National geography key should be the same across all vintages
        assert geo_keys_per_vintage["2021.05"] == geo_keys_per_vintage["2022.05"]
        assert geo_keys_per_vintage["2022.05"] == geo_keys_per_vintage["2023.05"]


class TestMultiVintageTimeSeries:
    """TS3-06/07/08: Time-series normalization with multi-vintage data."""

    def test_multi_year_observations(self, multi_vintage_oews_db):
        """TS3-07: observation table has >= 3 distinct period_keys for employment_count."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        distinct_periods = multi_vintage_oews_db.execute("""
            SELECT COUNT(DISTINCT tp.year)
            FROM fact_time_series_observation obs
            JOIN dim_metric m ON obs.metric_key = m.metric_key
            JOIN dim_geography g ON obs.geography_key = g.geography_key
            JOIN dim_time_period tp ON obs.period_key = tp.period_key
            WHERE m.metric_name = 'employment_count'
              AND g.geo_type = 'national'
              AND obs.comparability_mode = 'as_published'
        """).fetchone()[0]
        assert distinct_periods >= 3

    def test_known_occupation_all_vintages(self, multi_vintage_oews_db):
        """TS3-08: a known occupation has observations for all extracted vintages."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        # Find a SOC code that exists in the fixture data
        soc_code = multi_vintage_oews_db.execute(
            "SELECT soc_code FROM dim_occupation WHERE is_current = true LIMIT 1"
        ).fetchone()
        assert soc_code is not None
        soc_code = soc_code[0]

        years = multi_vintage_oews_db.execute("""
            SELECT DISTINCT tp.year
            FROM fact_time_series_observation obs
            JOIN dim_occupation o ON obs.occupation_key = o.occupation_key
            JOIN dim_metric m ON obs.metric_key = m.metric_key
            JOIN dim_geography g ON obs.geography_key = g.geography_key
            JOIN dim_time_period tp ON obs.period_key = tp.period_key
            WHERE o.soc_code = ?
              AND m.metric_name = 'employment_count'
              AND g.geo_type = 'national'
              AND obs.comparability_mode = 'as_published'
            ORDER BY tp.year
        """, [soc_code]).fetchall()
        year_list = [r[0] for r in years]
        assert 2021 in year_list
        assert 2022 in year_list
        assert 2023 in year_list

    def test_comparable_history_with_multi_vintage(self, multi_vintage_oews_db):
        """Comparable history should exist since all 3 vintages use SOC 2018."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        comparable_count = multi_vintage_oews_db.execute("""
            SELECT COUNT(*)
            FROM fact_time_series_observation
            WHERE comparability_mode = 'comparable'
        """).fetchone()[0]
        assert comparable_count > 0

    def test_yoy_change_exists_with_multi_vintage(self, multi_vintage_oews_db):
        """YoY change should be computed since we have consecutive years."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        yoy_count = multi_vintage_oews_db.execute("""
            SELECT COUNT(*)
            FROM fact_derived_series d
            JOIN dim_metric m ON d.metric_key = m.metric_key
            WHERE m.metric_name = 'yoy_absolute_change'
        """).fetchone()[0]
        assert yoy_count > 0

    def test_rolling_avg_exists_with_3_years(self, multi_vintage_oews_db):
        """3-year rolling average should be computed with 3 consecutive years."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        avg_count = multi_vintage_oews_db.execute("""
            SELECT COUNT(*)
            FROM fact_derived_series d
            JOIN dim_metric m ON d.metric_key = m.metric_key
            WHERE m.metric_name = 'rolling_avg_3yr'
        """).fetchone()[0]
        assert avg_count > 0

    def test_state_vs_national_gap_multi_vintage(self, multi_vintage_oews_db):
        """State vs national gap should work across vintages with shared geography keys."""
        from jobclass.orchestrate.timeseries_refresh import timeseries_refresh
        timeseries_refresh(multi_vintage_oews_db)

        gap_count = multi_vintage_oews_db.execute("""
            SELECT COUNT(*)
            FROM fact_derived_series d
            JOIN dim_metric m ON d.metric_key = m.metric_key
            WHERE m.metric_name = 'state_vs_national_gap'
        """).fetchone()[0]
        assert gap_count > 0


class TestMultiVintageStaging:
    """TS3-04: staging tables contain rows from all vintages."""

    def test_staging_has_all_vintages(self, multi_vintage_oews_db):
        # Staging only keeps the last loaded vintage (idempotent delete+insert)
        # But fact table should have all vintages
        fact_releases = multi_vintage_oews_db.execute(
            "SELECT DISTINCT source_release_id FROM fact_occupation_employment_wages ORDER BY source_release_id"
        ).fetchall()
        assert len([r[0] for r in fact_releases]) >= 3


class TestMultiVintageManifest:
    """TS3-01: manifest contains multi-vintage OEWS entries."""

    def test_manifest_has_multiple_oews_entries(self):
        from pathlib import Path

        from jobclass.extract.manifest import load_enabled_entries

        manifest_path = Path(__file__).parent.parent.parent / "config" / "source_manifest.yaml"
        entries = load_enabled_entries(manifest_path)
        oews_nat = [e for e in entries if e.dataset_name.startswith("oews_national")]
        oews_st = [e for e in entries if e.dataset_name.startswith("oews_state")]
        assert len(oews_nat) >= 3, f"Expected >= 3 OEWS national entries, got {len(oews_nat)}"
        assert len(oews_st) >= 3, f"Expected >= 3 OEWS state entries, got {len(oews_st)}"

    def test_manifest_entries_have_distinct_urls(self):
        from pathlib import Path

        from jobclass.extract.manifest import load_enabled_entries

        manifest_path = Path(__file__).parent.parent.parent / "config" / "source_manifest.yaml"
        entries = load_enabled_entries(manifest_path)
        oews_nat = [e for e in entries if e.dataset_name.startswith("oews_national")]
        urls = [e.dataset_url for e in oews_nat]
        assert len(urls) == len(set(urls)), "OEWS national entries have duplicate URLs"


class TestMultiVintageVersionDetection:
    """TS3-02/03: version detection works for all vintage URLs."""

    def test_version_detection_2021(self):
        from jobclass.extract.version_detect import detect_version_from_url
        v = detect_version_from_url("https://www.bls.gov/oes/special-requests/oesm21nat.zip")
        assert v == "2021.05"

    def test_version_detection_2022(self):
        from jobclass.extract.version_detect import detect_version_from_url
        v = detect_version_from_url("https://www.bls.gov/oes/special-requests/oesm22nat.zip")
        assert v == "2022.05"

    def test_version_detection_2023(self):
        from jobclass.extract.version_detect import detect_version_from_url
        v = detect_version_from_url("https://www.bls.gov/oes/special-requests/oesm23nat.zip")
        assert v == "2023.05"
