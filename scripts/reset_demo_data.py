"""One-command local SQLite demo reset and seed.

Runs the guarded demo reset workflow with backup, destructive reset, and clean
seed data. This is intended for local screenshot/demo preparation only.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import demo_reset_seed


def main() -> int:
    print(demo_reset_seed.LOCAL_ONLY_MESSAGE)
    try:
        db_path = demo_reset_seed.sqlite_db_path(demo_reset_seed.settings.DATABASE_URL)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"DATABASE_URL: {demo_reset_seed.settings.DATABASE_URL}")
    print(f"SQLite DB path: {db_path}")
    demo_reset_seed.backup_database(db_path)
    demo_reset_seed.init_db()
    with demo_reset_seed.SessionLocal() as db:
        demo_reset_seed.reset_demo_data(db)
        demo_reset_seed.print_seed_summary(demo_reset_seed.seed_demo_data(db))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
