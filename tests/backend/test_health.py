from app.backend.api.routes.health import health_check, readiness_check


def test_health_check() -> None:
    assert health_check() == {"status": "ok", "service": "TriageAI API"}


def test_readiness_check() -> None:
    response = readiness_check()

    assert response["status"] == "ready"
    assert response["database"] == "connected"
    assert "model_loaded" in response
    assert isinstance(response["model_loaded"], bool)
    assert "model_version" in response
    assert response["model_version"] in {None, "esi_345_lightgbm_v2_threshold"}

    if response["model_loaded"]:
        assert response.get("model_error") is None
    else:
        model_error = response.get("model_error")
        assert model_error is None or isinstance(model_error, str)
