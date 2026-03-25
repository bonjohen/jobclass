"""CPI domain expansion parser and schema contract tests."""

from pathlib import Path

import pytest

from jobclass.parse.cpi_domain import (
    _classify_area_type,
    _classify_semantic_role,
    _infer_parents,
    parse_cpi_area,
    parse_cpi_average_prices,
    parse_cpi_item_hierarchy,
    parse_cpi_observations,
    parse_cpi_series,
    validate_series_decomposition,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def cpi_item_content():
    return (FIXTURES_DIR / "cpi_item_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def cpi_area_content():
    return (FIXTURES_DIR / "cpi_area_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def cpi_series_content():
    return (FIXTURES_DIR / "cpi_series_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def cpi_data_content():
    return (FIXTURES_DIR / "cpi_data_sample.txt").read_text(encoding="utf-8")


@pytest.fixture
def cpi_avg_price_content():
    return (FIXTURES_DIR / "cpi_average_price_sample.txt").read_text(encoding="utf-8")


# ============================================================
# Item hierarchy parser tests
# ============================================================


class TestCpiItemHierarchyParser:
    def test_parses_all_items(self, cpi_item_content):
        rows = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        assert len(rows) == 16

    def test_item_fields(self, cpi_item_content):
        rows = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        sa0 = next(r for r in rows if r.item_code == "SA0")
        assert sa0.item_name == "All items"
        assert sa0.display_level == 0
        assert sa0.selectable is True
        assert sa0.source_release_id == "test-release"

    def test_hierarchy_levels_assigned(self, cpi_item_content):
        rows = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        by_code = {r.item_code: r for r in rows}
        assert by_code["SA0"].hierarchy_level == "All items"
        assert by_code["SAF1"].hierarchy_level == "Major group"
        assert by_code["SAF11"].hierarchy_level == "Intermediate aggregate"
        assert by_code["SAF111"].hierarchy_level == "Expenditure class"
        assert by_code["SAF1111"].hierarchy_level == "Item stratum"

    def test_parent_inference(self, cpi_item_content):
        rows = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        by_code = {r.item_code: r for r in rows}
        # All level-0 items are root peers (no parent) — BLS uses display_level=0
        # for All Items, major groups, and special aggregates
        assert by_code["SA0"].parent_item_code is None
        assert by_code["SAF"].parent_item_code is None  # Major group, level 0
        assert by_code["SAH"].parent_item_code is None  # Major group, level 0
        # Level-1 items parent to the most recent level-0 item
        assert by_code["SAF1"].parent_item_code == "SAF"
        # Level-2 items parent to the most recent level-1 item
        assert by_code["SAF11"].parent_item_code == "SAF1"
        # Level-3 under level-2
        assert by_code["SAF111"].parent_item_code == "SAF11"
        # Level-4 under level-3
        assert by_code["SAF1111"].parent_item_code == "SAF111"

    def test_empty_content(self):
        rows = parse_cpi_item_hierarchy("", "test")
        assert rows == []

    def test_header_only(self):
        rows = parse_cpi_item_hierarchy(
            "item_code\titem_name\tdisplay_level\tselectable\tsort_sequence\n", "test"
        )
        assert rows == []

    def test_metadata_populated(self, cpi_item_content):
        rows = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        for r in rows:
            assert r.source_release_id == "test-release"
            assert r.parser_version == "2.0.0"


# ============================================================
# Area parser tests
# ============================================================


class TestCpiAreaParser:
    def test_parses_all_areas(self, cpi_area_content):
        rows = parse_cpi_area(cpi_area_content, "test-release")
        assert len(rows) == 11

    def test_area_fields(self, cpi_area_content):
        rows = parse_cpi_area(cpi_area_content, "test-release")
        national = next(r for r in rows if r.area_code == "0000")
        assert national.area_title == "U.S. city average"
        assert national.area_type == "national"
        assert national.display_level == 0
        assert national.selectable is True

    def test_area_type_classification(self, cpi_area_content):
        rows = parse_cpi_area(cpi_area_content, "test-release")
        by_code = {r.area_code: r for r in rows}
        assert by_code["0000"].area_type == "national"
        assert by_code["0100"].area_type == "region"
        assert by_code["0110"].area_type == "division"
        assert by_code["A104"].area_type == "size_class"
        assert by_code["S12A"].area_type == "metro"

    def test_empty_content(self):
        rows = parse_cpi_area("", "test")
        assert rows == []


# ============================================================
# Series metadata parser tests
# ============================================================


class TestCpiSeriesParser:
    def test_parses_all_series(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        assert len(rows) == 8

    def test_series_decomposition(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        sa = next(r for r in rows if r.series_id == "CUSR0000SA0")
        assert sa.area_code == "0000"
        assert sa.item_code == "SA0"
        assert sa.seasonal_adjustment == "S"
        assert sa.periodicity == "R"
        assert sa.base_period == "1982-84=100"

    def test_unadjusted_series(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        ua = next(r for r in rows if r.series_id == "CUUR0000SA0")
        assert ua.seasonal_adjustment == "U"
        assert ua.periodicity == "R"

    def test_regional_series(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        ne = next(r for r in rows if r.series_id == "CUUR0100SA0")
        assert ne.area_code == "0100"

    def test_semi_annual_series(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        sa = next(r for r in rows if r.series_id == "CUSS0000SA0")
        assert sa.periodicity == "S"

    def test_year_range(self, cpi_series_content):
        rows = parse_cpi_series(cpi_series_content, "test-release")
        sa = next(r for r in rows if r.series_id == "CUSR0000SA0")
        assert sa.begin_year == 1947
        assert sa.end_year == 2026

    def test_empty_content(self):
        rows = parse_cpi_series("", "test")
        assert rows == []


# ============================================================
# Observation parser tests
# ============================================================


class TestCpiObservationParser:
    def test_parses_all_observations(self, cpi_data_content):
        rows = parse_cpi_observations(cpi_data_content, "test-release")
        assert len(rows) == 11

    def test_observation_fields(self, cpi_data_content):
        rows = parse_cpi_observations(cpi_data_content, "test-release")
        first = rows[0]
        assert first.series_id == "CUSR0000SA0"
        assert first.year == 2023
        assert first.period == "M01"
        assert abs(first.value - 299.170) < 0.001

    def test_parses_all_series_not_just_allitems(self, cpi_data_content):
        """Unlike cpi.py deflator, this parser keeps all series."""
        rows = parse_cpi_observations(cpi_data_content, "test-release")
        series_ids = {r.series_id for r in rows}
        assert len(series_ids) > 1
        assert "CUSR0000SAF" in series_ids
        assert "CUSR0000SAH" in series_ids
        assert "CUUR0100SA0" in series_ids

    def test_parses_all_periods_not_just_m13(self, cpi_data_content):
        """Unlike cpi.py deflator, this parser keeps all periods."""
        rows = parse_cpi_observations(cpi_data_content, "test-release")
        periods = {r.period for r in rows}
        assert "M01" in periods
        assert "M02" in periods
        assert "M13" in periods

    def test_empty_content(self):
        rows = parse_cpi_observations("", "test")
        assert rows == []


# ============================================================
# Average price parser tests
# ============================================================


class TestCpiAveragePriceParser:
    def test_parses_all_rows(self, cpi_avg_price_content):
        rows = parse_cpi_average_prices(cpi_avg_price_content, "test-release")
        assert len(rows) == 7

    def test_series_id_decomposition(self, cpi_avg_price_content):
        rows = parse_cpi_average_prices(cpi_avg_price_content, "test-release")
        first = rows[0]
        assert first.series_id == "APU0000708111"
        assert first.area_code == "0000"
        assert first.item_code == "708111"

    def test_regional_average_price(self, cpi_avg_price_content):
        rows = parse_cpi_average_prices(cpi_avg_price_content, "test-release")
        regional = next(r for r in rows if r.area_code == "0100")
        assert regional.series_id == "APU010074714"
        assert regional.item_code == "74714"

    def test_price_values(self, cpi_avg_price_content):
        rows = parse_cpi_average_prices(cpi_avg_price_content, "test-release")
        first = rows[0]
        assert abs(first.average_price - 4.897) < 0.001

    def test_empty_content(self):
        rows = parse_cpi_average_prices("", "test")
        assert rows == []


# ============================================================
# Semantic role and area type classifiers
# ============================================================


class TestClassifiers:
    def test_hierarchy_node(self):
        assert _classify_semantic_role("SA0") == "hierarchy_node"
        assert _classify_semantic_role("SAF") == "hierarchy_node"
        assert _classify_semantic_role("SAH1") == "hierarchy_node"

    def test_special_aggregate(self):
        assert _classify_semantic_role("SA0L1") == "special_aggregate"
        assert _classify_semantic_role("SA0L1E") == "special_aggregate"
        assert _classify_semantic_role("SA0L12") == "special_aggregate"
        assert _classify_semantic_role("SA0E") == "special_aggregate"

    def test_purchasing_power(self):
        assert _classify_semantic_role("SA0R") == "purchasing_power"

    def test_average_price_item(self):
        assert _classify_semantic_role("SS47014") == "average_price_item"

    def test_area_type_national(self):
        assert _classify_area_type("0000") == "national"

    def test_area_type_region(self):
        assert _classify_area_type("0100") == "region"
        assert _classify_area_type("0200") == "region"

    def test_area_type_division(self):
        assert _classify_area_type("0110") == "division"
        assert _classify_area_type("0350") == "division"

    def test_area_type_size_class(self):
        assert _classify_area_type("A104") == "size_class"
        assert _classify_area_type("D200") == "size_class"

    def test_area_type_metro(self):
        assert _classify_area_type("S12A") == "metro"
        assert _classify_area_type("S49E") == "metro"


# ============================================================
# Parent inference tests
# ============================================================


class TestParentInference:
    def test_simple_tree(self):
        items = [("A", 0), ("B", 1), ("C", 2), ("D", 1)]
        parents = _infer_parents(items)
        assert parents["A"] is None
        assert parents["B"] == "A"
        assert parents["C"] == "B"
        assert parents["D"] == "A"

    def test_flat_siblings(self):
        items = [("A", 0), ("B", 0), ("C", 0)]
        parents = _infer_parents(items)
        assert parents["A"] is None
        assert parents["B"] is None
        assert parents["C"] is None


# ============================================================
# Series decomposition validator
# ============================================================


class TestSeriesDecompositionValidator:
    def test_valid_decomposition(self, cpi_series_content):
        series = parse_cpi_series(cpi_series_content, "test-release")
        known_items = {"SA0", "SAF", "SAH", "SA0L1E", "SETB"}
        known_areas = {"0000", "0100"}
        warnings = validate_series_decomposition(series, known_items, known_areas)
        # Only CUSS0000SA0 has SA0 which IS in known_items, so no item warnings for it
        # But series with item_code not in the set will warn
        item_warnings = [w for w in warnings if "item_code" in w]
        assert len(item_warnings) == 0  # all item codes are in the known set

    def test_unknown_items_flagged(self):
        from jobclass.parse.cpi_domain import CpiSeriesRow

        series = [CpiSeriesRow(
            series_id="CUSR0000SXYZ",
            area_code="0000",
            item_code="SXYZ",
            seasonal_adjustment="S",
            periodicity="R",
            base_code="S",
            base_period="1982-84=100",
            series_title="Unknown",
            begin_year=2020,
            end_year=2026,
            source_release_id="test",
            parser_version="2.0.0",
        )]
        warnings = validate_series_decomposition(series, {"SA0"}, {"0000"})
        assert len(warnings) == 1
        assert "SXYZ" in warnings[0]


# ============================================================
# Schema contract tests (CPI2-10)
# ============================================================


class TestCpiStagingSchemaContracts:
    """Verify that staging tables exist with expected columns after migration."""

    def test_stage_cpi_series_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'stage__bls__cpi_series'"
            ).fetchall()
        }
        expected = {
            "series_id", "index_family", "seasonal_adjustment", "periodicity",
            "area_code", "item_code", "source_release_id", "parser_version",
        }
        assert expected.issubset(cols)

    def test_stage_cpi_item_hierarchy_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'stage__bls__cpi_item_hierarchy'"
            ).fetchall()
        }
        expected = {
            "item_code", "item_name", "hierarchy_level", "parent_item_code",
            "source_release_id", "parser_version",
        }
        assert expected.issubset(cols)

    def test_stage_cpi_publication_level_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'stage__bls__cpi_publication_level'"
            ).fetchall()
        }
        expected = {
            "item_code", "item_name", "area_type", "published",
            "source_release_id", "parser_version",
        }
        assert expected.issubset(cols)

    def test_stage_cpi_relative_importance_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'stage__bls__cpi_relative_importance'"
            ).fetchall()
        }
        expected = {
            "item_code", "area_code", "reference_period", "relative_importance",
            "source_release_id", "parser_version",
        }
        assert expected.issubset(cols)

    def test_stage_cpi_average_price_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'stage__bls__cpi_average_price'"
            ).fetchall()
        }
        expected = {
            "item_code", "area_code", "year", "period", "average_price",
            "source_release_id", "parser_version",
        }
        assert expected.issubset(cols)

    def test_dim_cpi_member_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'dim_cpi_member'"
            ).fetchall()
        }
        expected = {
            "member_key", "member_code", "title", "hierarchy_level",
            "semantic_role", "is_cross_cutting", "has_average_price",
            "has_relative_importance", "source_version",
        }
        assert expected.issubset(cols)

    def test_dim_cpi_area_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'dim_cpi_area'"
            ).fetchall()
        }
        expected = {
            "area_key", "area_code", "area_title", "area_type",
            "publication_frequency", "source_version",
        }
        assert expected.issubset(cols)

    def test_dim_cpi_series_variant_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'dim_cpi_series_variant'"
            ).fetchall()
        }
        expected = {
            "variant_key", "series_id", "index_family", "seasonal_adjustment",
            "periodicity", "area_code", "item_code", "member_key", "area_key",
            "source_version",
        }
        assert expected.issubset(cols)

    def test_fact_cpi_observation_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'fact_cpi_observation'"
            ).fetchall()
        }
        expected = {
            "member_key", "area_key", "variant_key", "time_period_key",
            "index_value", "source_release_id",
        }
        assert expected.issubset(cols)

    def test_bridge_cpi_member_hierarchy_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'bridge_cpi_member_hierarchy'"
            ).fetchall()
        }
        expected = {
            "parent_member_key", "child_member_key", "hierarchy_depth",
            "source_version",
        }
        assert expected.issubset(cols)

    def test_bridge_cpi_member_relation_exists(self, migrated_db):
        cols = {
            row[0]
            for row in migrated_db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'bridge_cpi_member_relation'"
            ).fetchall()
        }
        expected = {
            "member_key_a", "member_key_b", "relation_type", "description",
            "source_version",
        }
        assert expected.issubset(cols)


# ============================================================
# Loader tests (CPI3)
# ============================================================


@pytest.fixture
def cpi_domain_loaded_db(migrated_db, cpi_item_content, cpi_area_content, cpi_series_content, cpi_data_content):
    """DB with CPI domain loaded through parse → dim → bridge → fact."""
    from jobclass.load.cpi_domain import (
        load_bridge_cpi_area_hierarchy,
        load_bridge_cpi_member_hierarchy,
        load_bridge_cpi_member_relation,
        load_cpi_item_hierarchy_staging,
        load_cpi_series_staging,
        load_dim_cpi_area,
        load_dim_cpi_member,
        load_dim_cpi_series_variant,
        load_fact_cpi_observation,
    )

    items = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
    areas = parse_cpi_area(cpi_area_content, "test-release")
    series = parse_cpi_series(cpi_series_content, "test-release")
    observations = parse_cpi_observations(cpi_data_content, "test-release")

    load_cpi_item_hierarchy_staging(migrated_db, items, "test-release")
    load_cpi_series_staging(migrated_db, series, "test-release")
    load_dim_cpi_member(migrated_db, items, "test-release")
    load_dim_cpi_area(migrated_db, areas, "test-release")
    load_dim_cpi_series_variant(migrated_db, series, "test-release")
    load_bridge_cpi_member_hierarchy(migrated_db, items, "test-release")
    load_bridge_cpi_member_relation(migrated_db, items, "test-release")
    load_bridge_cpi_area_hierarchy(migrated_db, areas, "test-release")

    # Populate time periods so fact observation joins work
    for year in [2023, 2024]:
        migrated_db.execute(
            """INSERT INTO dim_time_period (period_type, year, quarter, period_start_date, period_end_date)
               VALUES ('annual', ?, NULL, ?, ?)""",
            [year, f"{year}-01-01", f"{year}-12-31"],
        )

    load_fact_cpi_observation(migrated_db, observations, "test-release", "test-release")
    return migrated_db


class TestCpiDomainLoaders:
    def test_dim_cpi_member_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_cpi_member"
        ).fetchone()[0]
        assert count == 16  # matches fixture items

    def test_dim_cpi_member_semantic_roles(self, cpi_domain_loaded_db):
        roles = {
            row[0]
            for row in cpi_domain_loaded_db.execute(
                "SELECT DISTINCT semantic_role FROM dim_cpi_member"
            ).fetchall()
        }
        assert "hierarchy_node" in roles
        assert "special_aggregate" in roles
        assert "purchasing_power" in roles

    def test_dim_cpi_area_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_cpi_area"
        ).fetchone()[0]
        assert count == 11  # matches fixture areas

    def test_dim_cpi_area_types(self, cpi_domain_loaded_db):
        types = {
            row[0]
            for row in cpi_domain_loaded_db.execute(
                "SELECT DISTINCT area_type FROM dim_cpi_area"
            ).fetchall()
        }
        assert "national" in types
        assert "region" in types
        assert "metro" in types

    def test_bridge_member_hierarchy_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM bridge_cpi_member_hierarchy"
        ).fetchone()[0]
        # Items with parent_item_code set (non-root items with level > 0)
        assert count > 0

    def test_bridge_member_relation_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM bridge_cpi_member_relation"
        ).fetchone()[0]
        # Fixture has SA0L1, SA0L1E, SA0R which match known relations
        assert count >= 2

    def test_bridge_area_hierarchy_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM bridge_cpi_area_hierarchy"
        ).fetchone()[0]
        assert count > 0

    def test_series_variant_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_cpi_series_variant"
        ).fetchone()[0]
        assert count == 8  # matches fixture series

    def test_series_variant_foreign_keys_resolved(self, cpi_domain_loaded_db):
        """Verify member_key and area_key are populated on variants."""
        resolved = cpi_domain_loaded_db.execute(
            """SELECT COUNT(*) FROM dim_cpi_series_variant
               WHERE member_key IS NOT NULL AND area_key IS NOT NULL"""
        ).fetchone()[0]
        assert resolved > 0

    def test_fact_observation_loaded(self, cpi_domain_loaded_db):
        count = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM fact_cpi_observation"
        ).fetchone()[0]
        # Only M13 annual average observations match dim_time_period
        assert count > 0

    def test_staging_idempotent(self, migrated_db, cpi_item_content):
        from jobclass.load.cpi_domain import load_cpi_item_hierarchy_staging

        items = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        load_cpi_item_hierarchy_staging(migrated_db, items, "test-release")
        load_cpi_item_hierarchy_staging(migrated_db, items, "test-release")
        count = migrated_db.execute(
            "SELECT COUNT(*) FROM stage__bls__cpi_item_hierarchy"
        ).fetchone()[0]
        assert count == 16

    def test_dimension_idempotent(self, migrated_db, cpi_item_content):
        from jobclass.load.cpi_domain import load_dim_cpi_member

        items = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        load_dim_cpi_member(migrated_db, items, "test-release")
        load_dim_cpi_member(migrated_db, items, "test-release")
        count = migrated_db.execute(
            "SELECT COUNT(*) FROM dim_cpi_member"
        ).fetchone()[0]
        assert count == 16

    def test_full_pipeline_idempotent(self, cpi_domain_loaded_db, cpi_item_content,
                                       cpi_area_content, cpi_series_content, cpi_data_content):
        """Run the full pipeline a second time — no duplicate rows."""
        from jobclass.load.cpi_domain import (
            load_bridge_cpi_area_hierarchy,
            load_bridge_cpi_member_hierarchy,
            load_bridge_cpi_member_relation,
            load_cpi_item_hierarchy_staging,
            load_cpi_series_staging,
            load_dim_cpi_area,
            load_dim_cpi_member,
            load_dim_cpi_series_variant,
            load_fact_cpi_observation,
        )

        items = parse_cpi_item_hierarchy(cpi_item_content, "test-release")
        areas = parse_cpi_area(cpi_area_content, "test-release")
        series = parse_cpi_series(cpi_series_content, "test-release")
        observations = parse_cpi_observations(cpi_data_content, "test-release")

        # Capture counts before second run
        member_before = cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM dim_cpi_member").fetchone()[0]
        area_before = cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM dim_cpi_area").fetchone()[0]
        variant_before = cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM dim_cpi_series_variant").fetchone()[0]
        obs_before = cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM fact_cpi_observation").fetchone()[0]

        # Second run
        load_cpi_item_hierarchy_staging(cpi_domain_loaded_db, items, "test-release")
        load_cpi_series_staging(cpi_domain_loaded_db, series, "test-release")
        load_dim_cpi_member(cpi_domain_loaded_db, items, "test-release")
        load_dim_cpi_area(cpi_domain_loaded_db, areas, "test-release")
        load_dim_cpi_series_variant(cpi_domain_loaded_db, series, "test-release")
        load_bridge_cpi_member_hierarchy(cpi_domain_loaded_db, items, "test-release")
        load_bridge_cpi_member_relation(cpi_domain_loaded_db, items, "test-release")
        load_bridge_cpi_area_hierarchy(cpi_domain_loaded_db, areas, "test-release")
        load_fact_cpi_observation(cpi_domain_loaded_db, observations, "test-release", "test-release")

        # Counts unchanged
        assert cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM dim_cpi_member").fetchone()[0] == member_before
        assert cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM dim_cpi_area").fetchone()[0] == area_before
        variant_after = cpi_domain_loaded_db.execute(
            "SELECT COUNT(*) FROM dim_cpi_series_variant"
        ).fetchone()[0]
        assert variant_after == variant_before
        assert cpi_domain_loaded_db.execute("SELECT COUNT(*) FROM fact_cpi_observation").fetchone()[0] == obs_before


# ============================================================
# Revision vintage loader tests (CPI9)
# ============================================================


class TestCpiRevisionVintageLoader:
    def test_load_revision_vintage(self, cpi_domain_loaded_db):
        from jobclass.load.cpi_domain import load_fact_cpi_revision_vintage
        from jobclass.parse.cpi_domain import CpiRevisionVintageRow

        rows = [
            CpiRevisionVintageRow(
                item_code="SA0", area_code="0000", year=2023, period="M13",
                vintage_label="2024-Q1-preliminary", index_value=304.7,
                is_preliminary=True, source_release_id="test-release",
                parser_version="2.0.0",
            ),
            CpiRevisionVintageRow(
                item_code="SA0", area_code="0000", year=2023, period="M13",
                vintage_label="2024-Q3-final", index_value=304.5,
                is_preliminary=False, source_release_id="test-release",
                parser_version="2.0.0",
            ),
        ]
        count = load_fact_cpi_revision_vintage(
            cpi_domain_loaded_db, rows, "test-release", "test-release"
        )
        assert count == 2

        # Verify both vintages stored
        stored = cpi_domain_loaded_db.execute(
            "SELECT vintage_label, index_value, is_preliminary FROM fact_cpi_revision_vintage ORDER BY vintage_label"
        ).fetchall()
        assert len(stored) == 2
        assert stored[0][0] == "2024-Q1-preliminary"
        assert stored[0][2] is True
        assert stored[1][0] == "2024-Q3-final"
        assert stored[1][2] is False

    def test_revision_vintage_idempotent(self, cpi_domain_loaded_db):
        from jobclass.load.cpi_domain import load_fact_cpi_revision_vintage
        from jobclass.parse.cpi_domain import CpiRevisionVintageRow

        rows = [
            CpiRevisionVintageRow(
                item_code="SA0", area_code="0000", year=2023, period="M13",
                vintage_label="2024-Q1-preliminary", index_value=304.7,
                is_preliminary=True, source_release_id="test-release",
                parser_version="2.0.0",
            ),
        ]
        load_fact_cpi_revision_vintage(
            cpi_domain_loaded_db, rows, "test-release", "test-release"
        )
        # Second run — same grain, no duplicates
        count = load_fact_cpi_revision_vintage(
            cpi_domain_loaded_db, rows, "test-release", "test-release"
        )
        assert count == 0

    def test_revision_vintage_empty_rows(self, cpi_domain_loaded_db):
        from jobclass.load.cpi_domain import load_fact_cpi_revision_vintage

        count = load_fact_cpi_revision_vintage(
            cpi_domain_loaded_db, [], "test-release", "test-release"
        )
        assert count == 0

    def test_revision_vintage_unknown_member_skipped(self, cpi_domain_loaded_db):
        from jobclass.load.cpi_domain import load_fact_cpi_revision_vintage
        from jobclass.parse.cpi_domain import CpiRevisionVintageRow

        rows = [
            CpiRevisionVintageRow(
                item_code="ZZZZZ", area_code="0000", year=2023, period="M13",
                vintage_label="test", index_value=100.0,
                is_preliminary=True, source_release_id="test-release",
                parser_version="2.0.0",
            ),
        ]
        count = load_fact_cpi_revision_vintage(
            cpi_domain_loaded_db, rows, "test-release", "test-release"
        )
        assert count == 0
