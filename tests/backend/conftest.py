import os
import tempfile
from pathlib import Path

import pytest

TEST_DB_PATH = Path(tempfile.gettempdir()) / "triageai_test.sqlite"
os.environ["DATABASE_URL"] = os.environ.get("TRIAGEAI_TEST_DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")


@pytest.fixture(autouse=True)
def reset_test_database() -> None:
    from app.backend.db.base import Base, init_db
    from app.backend.db.session import engine

    Base.metadata.drop_all(bind=engine)
    init_db()


@pytest.fixture(autouse=True)
def legacy_contract_session(request):
    """Existing contract tests isolate domain behavior; security tests use real sessions."""
    if request.node.get_closest_marker("security"):
        yield
        return
    from app.backend.api.main import app
    from app.backend.core.security import get_authenticated_db
    from app.backend.db.session import get_db

    app.dependency_overrides[get_authenticated_db] = get_db
    yield
    app.dependency_overrides.pop(get_authenticated_db, None)
