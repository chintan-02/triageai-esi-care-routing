from fastapi.testclient import TestClient

from app.backend.api.main import app
from app.backend.api.routes.health import health_check
from app.backend.services.model_loader import ModelBundle


client = TestClient(app)


def test_health_check() -> None:
    assert health_check() == {"status": "ok", "service": "TriageAI API"}


def test_readiness_check_returns_stable_success_shape() -> None:
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    body = response.json()
    assert body["status"] in {"ready", "not_ready"}
    assert body["database"] in {"connected", "not_connected"}
    assert isinstance(body["model_loaded"], bool)
    assert "model_version" in body

    if body["status"] == "ready":
        assert response.status_code == 200
        assert body["database"] == "connected"
        assert body["model_loaded"] is True
        assert body["model_error"] is None
    else:
        assert response.status_code == 503
        model_error = body.get("model_error")
        assert model_error is None or isinstance(model_error, str)


def test_readiness_check_returns_503_when_model_unavailable(monkeypatch) -> None:
    from app.backend.api.routes import health

    monkeypatch.setattr(
        health,
        "get_model_bundle",
        lambda: ModelBundle(
            loaded=False,
            model_version="esi_345_lightgbm_v2_threshold",
            error_message="LightGBM package is not installed.",
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["database"] == "connected"
    assert body["model_loaded"] is False
    assert body["model_error"] == "LightGBM package is not installed."
