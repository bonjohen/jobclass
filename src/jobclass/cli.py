"""Command-line interface for the JobClass pipeline."""

from __future__ import annotations

import argparse
import sys

from jobclass.config.database import get_connection, apply_migrations
from jobclass.config.settings import DB_PATH


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jobclass-pipeline",
        description="JobClass labor market data pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("migrate", help="Apply pending database migrations")
    sub.add_parser("status", help="Show warehouse status and row counts")

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

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
