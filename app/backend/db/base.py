"""SQLAlchemy declarative base and local table initialization."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create database tables for local development and tests."""
    from app.backend.db import models  # noqa: F401
    from app.backend.db.session import engine

    Base.metadata.create_all(bind=engine)
