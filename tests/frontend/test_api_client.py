from app.frontend.streamlit_app.services import api_client


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> dict:
        return self._payload


def test_get_ready_status_parses_backend_response(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(
            200,
            {
                "status": "ready",
                "model_loaded": True,
                "model_version": "esi_345_lightgbm_v2_threshold",
                "database": "connected",
            },
        )

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.get_ready_status()

    assert result["ok"] is True
    assert result["backend_connected"] is True
    assert result["data"]["model_loaded"] is True


def test_submit_prediction_marks_placeholder_warning(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(
            200,
            {
                "request_id": "request-1",
                "model_loaded": False,
                "is_placeholder": True,
                "probabilities": {},
            },
        )

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.submit_prediction({"patient_age": 42, "chief_complaint": "Cough"})

    assert result["ok"] is True
    assert "fallback contract response" in result["message"]


def test_submit_prediction_formats_validation_error(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(422, {"detail": [{"loc": ["body", "patient_age"]}]})

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.submit_prediction({"patient_age": 121})

    assert result["ok"] is False
    assert result["error_type"] == "validation_error"
    assert result["data"]["detail"][0]["loc"] == ["body", "patient_age"]
