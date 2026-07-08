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
    assert "model_source" in body
    assert "selected_calibration_method" in body
    assert "threshold_config_loaded" in body
    assert "feature_count" in body
    assert "class_order" in body

    if body["status"] == "ready":
        assert response.status_code == 200
        assert body["database"] == "connected"
        assert body["model_loaded"] is True
        assert body["model_version"] == "lightgbm_v2_weight_threshold_esi345"
        assert body["model_source"] == "final_registry"
        assert body["selected_calibration_method"] == "raw_lightgbm_probability"
        assert body["threshold_config_loaded"] is True
        assert body["feature_count"] == 273
        assert body["class_order"] == ["ESI_3", "ESI_4", "ESI_5"]
        assert body["is_placeholder"] is False
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
            model_version="lightgbm_v2_weight_threshold_esi345",
            model_source="unavailable",
            selected_calibration_method="raw_lightgbm_probability",
            error_message="LightGBM package is not installed.",
        ),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["database"] == "connected"
    assert body["model_loaded"] is False
    assert body["model_source"] == "unavailable"
    assert body["model_error"] == "LightGBM package is not installed."
