"""T1-05: Database connection and migration framework execute without error."""

from jobclass.config.database import apply_migrations, get_applied_versions, rollback_migration


def test_migration_applies_cleanly(db, tmp_path):
    """Migration applies cleanly to empty database."""
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    (mdir / "001_test.sql").write_text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);")

    applied = apply_migrations(db, migrations_dir=mdir)
    assert applied == ["001_test.sql"]

    # Table exists
    result = db.execute("SELECT * FROM test_table").fetchall()
    assert result == []

    # Migration recorded
    versions = get_applied_versions(db)
    assert 1 in versions


def test_migration_is_idempotent(db, tmp_path):
    """Running migrations twice does not re-apply."""
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    (mdir / "001_test.sql").write_text("CREATE TABLE t1 (id INTEGER);")

    apply_migrations(db, migrations_dir=mdir)
    applied_second = apply_migrations(db, migrations_dir=mdir)
    assert applied_second == []


def test_multiple_migrations_in_order(db, tmp_path):
    """Multiple migrations applied in version order."""
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    (mdir / "001_first.sql").write_text("CREATE TABLE t1 (id INTEGER);")
    (mdir / "002_second.sql").write_text("CREATE TABLE t2 (id INTEGER);")

    applied = apply_migrations(db, migrations_dir=mdir)
    assert applied == ["001_first.sql", "002_second.sql"]
    assert get_applied_versions(db) == {1, 2}


def test_rollback_removes_version(db, tmp_path):
    """Rollback removes migration record."""
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    (mdir / "001_test.sql").write_text("CREATE TABLE t1 (id INTEGER);")

    apply_migrations(db, migrations_dir=mdir)
    assert 1 in get_applied_versions(db)

    rollback_migration(db, 1)
    assert 1 not in get_applied_versions(db)


def test_no_migrations_dir(db, tmp_path):
    """Missing migrations dir returns empty list."""
    applied = apply_migrations(db, migrations_dir=tmp_path / "nonexistent")
    assert applied == []
