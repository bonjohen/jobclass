"""T1-01: Configuration module loads defaults and environment overrides."""

from pathlib import Path


def test_get_config_returns_expected_keys():
    from jobclass.config.settings import get_config

    cfg = get_config()
    expected_keys = {
        "project_root",
        "db_path",
        "raw_root",
        "manifest_path",
        "migrations_dir",
        "timestamp_format",
        "checksum_algorithm",
        "download_max_retries",
        "download_backoff_seconds",
    }
    assert expected_keys == set(cfg.keys())


def test_config_defaults_are_paths():
    from jobclass.config.settings import get_config

    cfg = get_config()
    assert isinstance(cfg["project_root"], Path)
    assert isinstance(cfg["db_path"], Path)
    assert isinstance(cfg["raw_root"], Path)


def test_environment_override_db_path(monkeypatch):
    monkeypatch.setenv("JOBCLASS_DB_PATH", "/tmp/override.duckdb")
    # Re-import to pick up env change
    import importlib

    import jobclass.config.settings as settings_mod

    importlib.reload(settings_mod)
    assert Path("/tmp/override.duckdb") == settings_mod.DB_PATH
    # Restore
    monkeypatch.delenv("JOBCLASS_DB_PATH")
    importlib.reload(settings_mod)


def test_environment_override_raw_root(monkeypatch):
    monkeypatch.setenv("JOBCLASS_RAW_ROOT", "/tmp/raw_override")
    import importlib

    import jobclass.config.settings as settings_mod

    importlib.reload(settings_mod)
    assert Path("/tmp/raw_override") == settings_mod.RAW_ROOT
    monkeypatch.delenv("JOBCLASS_RAW_ROOT")
    importlib.reload(settings_mod)


def test_timestamp_format_is_utc():
    from jobclass.config.settings import TIMESTAMP_FORMAT

    assert "Z" in TIMESTAMP_FORMAT
