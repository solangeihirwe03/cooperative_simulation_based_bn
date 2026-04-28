"""Project-level migration entrypoint.

Run:
    python migrate.py
    python migrate.py --stamp-head
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Alembic migrations.")
    parser.add_argument(
        "--stamp-head",
        action="store_true",
        help="Mark the current database schema as up-to-date without running migrations.",
    )
    return parser


def main() -> None:
    """Run Alembic migrations to create/update database tables."""
    args = build_parser().parse_args()
    command = [
        sys.executable,
        "-m",
        "alembic",
        "stamp" if args.stamp_head else "upgrade",
        "head",
    ]
    try:
        subprocess.run(command, check=True)
        if args.stamp_head:
            print("Migration version stamped to head.")
        else:
            print("Migrations applied successfully.")
    except subprocess.CalledProcessError as exc:
        if not args.stamp_head:
            print(
                "Migration failed. If your tables already exist, run: python migrate.py --stamp-head"
            )
        raise SystemExit(exc.returncode)


if __name__ == "__main__":
    main()
