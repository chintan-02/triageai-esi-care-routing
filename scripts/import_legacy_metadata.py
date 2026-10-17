"""Recover local synthetic demo metadata. Default: inspect only; PDF bytes are not imported."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.core.config import settings
from app.backend.db.base import assert_schema_current
from app.backend.db.session import SessionLocal, engine
from app.backend.services.legacy_import import import_legacy_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--owner-email', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if settings.APP_ENV.lower() not in {'development', 'demo', 'test'} or engine.dialect.name != 'sqlite':
        parser.error('This recovery command is restricted to local/demo SQLite targets')
    assert_schema_current()
    source = args.source.resolve(strict=True)
    if source == Path(engine.url.database).resolve():
        parser.error('Source and target must be different database files')
    try:
        with SessionLocal() as db:
            result = import_legacy_metadata(db, source, args.owner_email, apply=args.apply)
    except ValueError as exc:
        parser.exit(1, f'Import refused: {exc}\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
