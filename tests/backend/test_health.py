from app.backend.api.routes.health import health_check, readiness_check


def test_health_check() -> None:
    assert health_check() == {"status": "ok", "service": "TriageAI API"}


def test_readiness_check() -> None:
    assert readiness_check() == {
        "status": "ready",
        "model_loaded": False,
        "database": "not_connected",
    }
