"""Operator-only retention command. Defaults to a read-only dry run."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.db.base import assert_schema_current
from app.backend.db.session import SessionLocal
from app.backend.services.demo_cleanup import cleanup_demo_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Delete eligible expired demo data and report objects")
    parser.add_argument("--batch-size", type=int, default=None)
    args = parser.parse_args()
    assert_schema_current()
    with SessionLocal() as db:
        summary = cleanup_demo_data(db, apply=args.apply, batch_size=args.batch_size)
    print(json.dumps(summary, sort_keys=True))
    return 1 if summary["failed_workspaces"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
