"""Command-line interface for the JobClass pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jobclass.config.database import apply_migrations, get_connection
from jobclass.config.settings import DB_PATH

_DEFAULT_MANIFEST = Path(__file__).parent.parent.parent / "config" / "source_manifest.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jobclass-pipeline",
        description="JobClass labor market data pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("migrate", help="Apply pending database migrations")
    sub.add_parser("status", help="Show warehouse status and row counts")

    run_all = sub.add_parser("run-all", help="Download all sources and load the warehouse")
    run_all.add_argument("--manifest", default=str(_DEFAULT_MANIFEST), help="Path to source manifest YAML")
    run_all.add_argument("--raw-dir", default="raw", help="Directory for immutable raw artifact storage")

    args = parser.parse_args()

    if args.command == "migrate":
        conn = get_connection(DB_PATH)
        applied = apply_migrations(conn)
        if applied:
            print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
        else:
            print("No pending migrations.")
        conn.close()

    elif args.command == "status":
        conn = get_connection(DB_PATH)
        apply_migrations(conn)
        tables = [
            "dim_occupation", "dim_geography", "dim_industry",
            "dim_skill", "dim_knowledge", "dim_ability", "dim_task",
            "fact_occupation_employment_wages", "fact_occupation_projections",
        ]
        print("Warehouse status:")
        for t in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t}: {count:,} rows")
            except Exception:
                print(f"  {t}: (not found)")
        conn.close()

    elif args.command == "run-all":
        from jobclass.orchestrate.run_all import run_all_pipelines

        conn = get_connection(DB_PATH)
        apply_migrations(conn)

        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"Manifest not found: {manifest_path}")
            sys.exit(1)

        raw_root = Path(args.raw_dir)
        raw_root.mkdir(parents=True, exist_ok=True)

        print(f"Running all pipelines from {manifest_path}")
        print(f"Database: {DB_PATH}")
        print(f"Raw storage: {raw_root}")

        summary = run_all_pipelines(conn, manifest_path, raw_root)

        print(f"\n{'='*50}")
        print("Pipeline run complete:")
        print(f"  Attempted: {summary.pipelines_attempted}")
        print(f"  Succeeded: {summary.pipelines_succeeded}")
        print(f"  Failed:    {summary.pipelines_failed}")
        if summary.errors:
            print("\nErrors:")
            for e in summary.errors:
                print(f"  {e}")

        conn.close()
        sys.exit(0 if summary.pipelines_failed == 0 else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
