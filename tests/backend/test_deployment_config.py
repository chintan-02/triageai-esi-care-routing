import pytest
from pydantic import ValidationError
from app.backend.core.config import Settings


def test_production_rejects_unsafe_defaults():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, APP_ENV="production")


def test_production_requires_explicit_database_storage_and_origins():
    config = dict(APP_ENV="production", DEBUG=False, AUTO_CREATE_TABLES=False,
                  DATABASE_URL="postgresql+psycopg://demo:password@db/triageai",
                  REPORT_STORAGE_BACKEND="gcs", REPORT_GCS_BUCKET="private-reports",
                  CORS_ALLOWED_ORIGINS=["https://triageai.example.test"])
    assert Settings(_env_file=None, **config).DEBUG is False
    for override in [{"DEBUG": True}, {"AUTO_CREATE_TABLES": True},
                     {"DATABASE_URL": "sqlite:///local.db"},
                     {"CORS_ALLOWED_ORIGINS": ["*"]}, {"REPORT_GCS_BUCKET": ""}]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{**config, **override})
