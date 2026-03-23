"""T2-08 through T2-13: Manifest reader and contract tests."""

from pathlib import Path

import pytest
import yaml

from jobclass.extract.manifest import load_enabled_entries, load_manifest

MANIFEST_PATH = Path(__file__).parent.parent.parent / "config" / "source_manifest.yaml"


class TestManifestReader:
    """T2-08: Manifest reader parses valid manifest."""

    def test_parses_valid_manifest(self):
        entries = load_manifest(MANIFEST_PATH)
        assert len(entries) > 0
        for entry in entries:
            assert entry.source_name
            assert entry.dataset_name
            assert entry.dataset_url
            assert entry.expected_format
            assert entry.parser_name

    def test_entries_have_enabled_flag(self):
        entries = load_manifest(MANIFEST_PATH)
        for entry in entries:
            assert isinstance(entry.enabled, bool)


class TestManifestValidation:
    """T2-09: Manifest reader rejects missing required fields."""

    def test_rejects_missing_fields(self, tmp_path):
        bad_manifest = tmp_path / "bad.yaml"
        bad_manifest.write_text(yaml.dump({
            "sources": [{"source_name": "test", "dataset_name": "test"}]
        }))
        with pytest.raises(ValueError, match="missing required fields"):
            load_manifest(bad_manifest)

    def test_rejects_missing_sources_key(self, tmp_path):
        bad_manifest = tmp_path / "empty.yaml"
        bad_manifest.write_text(yaml.dump({"other_key": []}))
        with pytest.raises(ValueError, match="missing 'sources' key"):
            load_manifest(bad_manifest)


class TestManifestFiltering:
    """T2-10: Manifest reader filters disabled entries."""

    def test_filters_disabled(self):
        all_entries = load_manifest(MANIFEST_PATH)
        enabled_entries = load_enabled_entries(MANIFEST_PATH)
        disabled_count = sum(1 for e in all_entries if not e.enabled)
        assert len(enabled_entries) == len(all_entries) - disabled_count
        for entry in enabled_entries:
            assert entry.enabled is True


class TestSocManifestContract:
    """T2-11: SOC manifest entries contain required fields."""

    def test_soc_entries_exist(self):
        entries = load_manifest(MANIFEST_PATH)
        soc_datasets = {e.dataset_name for e in entries if e.source_name == "soc"}
        assert "soc_hierarchy" in soc_datasets
        assert "soc_definitions" in soc_datasets

    def test_soc_entries_have_urls_and_parsers(self):
        entries = load_manifest(MANIFEST_PATH)
        for e in entries:
            if e.source_name == "soc":
                assert e.dataset_url.startswith("https://")
                assert e.parser_name
                assert e.expected_format


class TestOewsManifestContract:
    """T2-12: OEWS manifest entries contain required fields."""

    def test_oews_entries_exist(self):
        entries = load_manifest(MANIFEST_PATH)
        bls_datasets = {e.dataset_name for e in entries if e.source_name == "bls"}
        assert "oews_national" in bls_datasets
        assert "oews_state" in bls_datasets

    def test_oews_entries_have_urls_and_parsers(self):
        entries = load_manifest(MANIFEST_PATH)
        for e in entries:
            if e.dataset_name.startswith("oews_"):
                assert e.dataset_url.startswith("https://")
                assert e.parser_name
                assert e.expected_format


class TestOnetManifestContract:
    """T2-13: O*NET manifest entries contain required fields."""

    def test_onet_entries_exist(self):
        entries = load_manifest(MANIFEST_PATH)
        onet_datasets = {e.dataset_name for e in entries if e.source_name == "onet"}
        assert "onet_skills" in onet_datasets
        assert "onet_knowledge" in onet_datasets
        assert "onet_abilities" in onet_datasets
        assert "onet_tasks" in onet_datasets

    def test_onet_entries_have_urls_and_parsers(self):
        entries = load_manifest(MANIFEST_PATH)
        for e in entries:
            if e.source_name == "onet":
                assert e.dataset_url.startswith("https://")
                assert e.parser_name
                assert e.expected_format
