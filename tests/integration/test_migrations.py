"""Use an empty disposable database; CI supplies a real PostgreSQL instance."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("dialect", ["sqlite", "postgresql"])
def test_upgrade_preserves_legacy_rows_and_schema_matches_models(tmp_path, dialect):
    if dialect == "postgresql":
        url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
        if not url:
            pytest.skip("MIGRATION_TEST_DATABASE_URL is required for live PostgreSQL validation")
    else:
        url = f"sqlite:///{tmp_path / 'migration.sqlite'}"
    env = {**os.environ, "DATABASE_URL": url, "APP_ENV": "test", "DEBUG": "false"}
    def migrate(*args):
        result = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=ROOT,
                                env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
    migrate("upgrade", "2dc4cd53d258")
    schema_check = [sys.executable, "-c", "from app.backend.db.base import assert_schema_current; assert_schema_current()"]
    outdated = subprocess.run(schema_check, cwd=ROOT, env=env, capture_output=True, text=True)
    assert outdated.returncode != 0
    assert "migrations are not current" in outdated.stderr
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO patients (id, age, created_at, updated_at) VALUES ('legacy-patient', 42, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO assessments (id, patient_id, chief_complaint, status, created_at, updated_at) VALUES ('legacy-assessment', 'legacy-patient', 'Synthetic case', 'pending_review', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
    migrate("upgrade", "0002_sessions_storage")
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO users (id, role, created_at, updated_at) VALUES ('legacy-owner', 'Doctor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), ('legacy-admin', 'Admin', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO assessments (id, owner_id, patient_id, chief_complaint, status, created_at, updated_at) VALUES ('owned-legacy', 'legacy-owner', 'legacy-patient', 'Owned synthetic case', 'pending_review', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO reports (id, assessment_id, report_status, include_audit, created_at) VALUES ('legacy-report', 'owned-legacy', 'queued', true, CURRENT_TIMESTAMP)"))
    migrate("upgrade", "head")
    migrate("upgrade", "head")
    migrate("check")
    current = subprocess.run(schema_check, cwd=ROOT, env=env, capture_output=True, text=True)
    assert current.returncode == 0, current.stderr
    assert "auth_sessions" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        row = connection.execute(text("SELECT chief_complaint, owner_id FROM assessments WHERE id='legacy-assessment'")).one()
        assert row == ("Synthetic case", None)
        quota = connection.execute(text("SELECT is_demo, assessment_count, report_count FROM users WHERE id='legacy-owner'")).one()
        assert quota == (True, 1, 1)
        assert connection.execute(text("SELECT is_demo FROM users WHERE id='legacy-admin'")).scalar() in (False, 0)
    migrate("downgrade", "2dc4cd53d258")
    migrate("upgrade", "head")
    migrate("check")
    # Leave the disposable database empty for repeatable CI runs.
    migrate("downgrade", "base")
    engine.dispose()
