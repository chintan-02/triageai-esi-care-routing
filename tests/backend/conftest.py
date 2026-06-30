import os
import tempfile
from pathlib import Path

import pytest

TEST_DB_PATH = Path(tempfile.gettempdir()) / "triageai_test.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(autouse=True)
def reset_test_database() -> None:
    from app.backend.db.base import Base, init_db
    from app.backend.db.session import engine

    Base.metadata.drop_all(bind=engine)
    init_db()
