"""SQLAlchemy declarative base and local table initialization."""

from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create database tables for local development and tests."""
    from app.backend.db import models  # noqa: F401
    from app.backend.db.session import engine

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_compat_columns(engine)


def _ensure_sqlite_compat_columns(engine: object) -> None:
    dialect = getattr(engine, "dialect", None)
    if getattr(dialect, "name", None) != "sqlite":
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "patients" in table_names:
            existing_patient_columns = {
                column["name"] for column in inspector.get_columns("patients")
            }
            if "name" not in existing_patient_columns:
                connection.execute(text("ALTER TABLE patients ADD COLUMN name VARCHAR"))
            if "mrn" not in existing_patient_columns:
                connection.execute(text("ALTER TABLE patients ADD COLUMN mrn VARCHAR"))

        if "predictions" in table_names:
            existing_prediction_columns = {
                column["name"] for column in inspector.get_columns("predictions")
            }
            if "latency_ms" not in existing_prediction_columns:
                connection.execute(text("ALTER TABLE predictions ADD COLUMN latency_ms INTEGER"))

        if "assessments" in table_names:
            existing_assessment_columns = {
                column["name"] for column in inspector.get_columns("assessments")
            }
            if "risk_flags_json" not in existing_assessment_columns:
                connection.execute(
                    text("ALTER TABLE assessments ADD COLUMN risk_flags_json TEXT")
                )
            if "comorbidities_json" not in existing_assessment_columns:
                connection.execute(
                    text("ALTER TABLE assessments ADD COLUMN comorbidities_json TEXT")
                )


def assert_schema_current() -> None:
    """Deployment startup verifies migrations, never mutates the schema."""
    from pathlib import Path
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from app.backend.db.session import engine
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    expected = set(ScriptDirectory.from_config(config).get_heads())
    with engine.connect() as connection:
        actual = set(MigrationContext.configure(connection).get_current_heads())
    if actual != expected:
        raise RuntimeError("Database migrations are not current; run alembic upgrade head before deployment")
