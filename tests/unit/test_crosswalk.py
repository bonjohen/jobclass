"""NDS7: SOC 2010↔2018 crosswalk parser and loader tests."""

from pathlib import Path

import pytest

from jobclass.parse.soc import parse_soc_crosswalk

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def crosswalk_content():
    return (FIXTURES_DIR / "soc_crosswalk_sample.csv").read_text(encoding="utf-8")


# ============================================================
# Parser tests
# ============================================================


class TestCrosswalkParser:
    def test_parses_all_rows(self, crosswalk_content):
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        assert len(rows) == 10

    def test_versions_set(self, crosswalk_content):
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        for r in rows:
            assert r.source_soc_version == "2010"
            assert r.target_soc_version == "2018"

    def test_metadata(self, crosswalk_content):
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        for r in rows:
            assert r.source_release_id == "test-release"
            assert r.parser_version is not None

    def test_one_to_one_classification(self, crosswalk_content):
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        by_pair = {(r.source_soc_code, r.target_soc_code): r.mapping_type for r in rows}
        assert by_pair[("11-1011", "11-1011")] == "1:1"
        assert by_pair[("11-1021", "11-1021")] == "1:1"
        assert by_pair[("15-1131", "15-1251")] == "1:1"
        assert by_pair[("29-1061", "29-1211")] == "1:1"

    def test_split_classification(self, crosswalk_content):
        """One 2010 code maps to multiple 2018 codes."""
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        by_pair = {(r.source_soc_code, r.target_soc_code): r.mapping_type for r in rows}
        # 15-1134 splits into 15-1254 and 15-1255
        assert by_pair[("15-1134", "15-1254")] == "split"
        assert by_pair[("15-1134", "15-1255")] == "split"
        # 29-1062 splits into 29-1215 and 29-1216
        assert by_pair[("29-1062", "29-1215")] == "split"
        assert by_pair[("29-1062", "29-1216")] == "split"

    def test_merge_classification(self, crosswalk_content):
        """Multiple 2010 codes map to one 2018 code."""
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        by_pair = {(r.source_soc_code, r.target_soc_code): r.mapping_type for r in rows}
        # 15-1132 and 15-1133 both map to 15-1256
        assert by_pair[("15-1132", "15-1256")] == "merge"
        assert by_pair[("15-1133", "15-1256")] == "merge"

    def test_titles_preserved(self, crosswalk_content):
        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        by_src = {r.source_soc_code: r.source_soc_title for r in rows}
        assert by_src["11-1011"] == "Chief Executives"

    def test_empty_content(self):
        rows = parse_soc_crosswalk("", "test")
        assert rows == []


# ============================================================
# Loader tests
# ============================================================


class TestCrosswalkLoader:
    def test_staging_load(self, migrated_db, crosswalk_content):
        from jobclass.load.soc import load_crosswalk_staging

        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        count = load_crosswalk_staging(migrated_db, rows, "test-release")
        assert count == 10
        db_count = migrated_db.execute("SELECT COUNT(*) FROM stage__soc__crosswalk").fetchone()[0]
        assert db_count == 10

    def test_staging_idempotent(self, migrated_db, crosswalk_content):
        from jobclass.load.soc import load_crosswalk_staging

        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        load_crosswalk_staging(migrated_db, rows, "test-release")
        load_crosswalk_staging(migrated_db, rows, "test-release")
        db_count = migrated_db.execute("SELECT COUNT(*) FROM stage__soc__crosswalk").fetchone()[0]
        assert db_count == 10

    def test_bridge_load(self, migrated_db, crosswalk_content):
        from jobclass.load.soc import load_bridge_soc_crosswalk, load_crosswalk_staging

        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        load_crosswalk_staging(migrated_db, rows, "test-release")
        count = load_bridge_soc_crosswalk(migrated_db, "test-release")
        assert count == 10

    def test_bridge_idempotent(self, migrated_db, crosswalk_content):
        from jobclass.load.soc import load_bridge_soc_crosswalk, load_crosswalk_staging

        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        load_crosswalk_staging(migrated_db, rows, "test-release")
        load_bridge_soc_crosswalk(migrated_db, "test-release")
        load_bridge_soc_crosswalk(migrated_db, "test-release")
        db_count = migrated_db.execute("SELECT COUNT(*) FROM bridge_soc_crosswalk").fetchone()[0]
        assert db_count == 10

    def test_mapping_types_in_bridge(self, migrated_db, crosswalk_content):
        from jobclass.load.soc import load_bridge_soc_crosswalk, load_crosswalk_staging

        rows = parse_soc_crosswalk(crosswalk_content, "test-release")
        load_crosswalk_staging(migrated_db, rows, "test-release")
        load_bridge_soc_crosswalk(migrated_db, "test-release")

        types = migrated_db.execute(
            "SELECT DISTINCT mapping_type FROM bridge_soc_crosswalk ORDER BY mapping_type"
        ).fetchall()
        type_set = {r[0] for r in types}
        assert type_set == {"1:1", "merge", "split"}
