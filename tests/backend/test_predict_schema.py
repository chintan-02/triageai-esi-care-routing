from fastapi.testclient import TestClient

from app.backend.api.main import app
from app.backend.schemas.intake import PatientIntakeRequest


client = TestClient(app)


def valid_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "chief_complaint": "Chest discomfort",
        "pain_score": 6,
        "oxygen_saturation": 98.0,
    }


def test_patient_intake_schema_validates_bounds() -> None:
    intake = PatientIntakeRequest(**valid_intake_payload())

    assert intake.patient_age == 42
    assert intake.chief_complaint == "Chest discomfort"


def test_predict_returns_model_aware_response() -> None:
    response = client.post("/predict", json=valid_intake_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"]
    assert body["acuity_scale"] == "ESI"
    assert "model_loaded" in body
    assert isinstance(body["model_loaded"], bool)

    if body["model_loaded"]:
        assert body["is_placeholder"] is False
        assert body["model_version"] == "lightgbm_v2_weight_threshold_esi345"
        assert body["selected_calibration_method"] == "raw_lightgbm_probability"
        assert body["predicted_esi"] in [3, 4, 5]
        assert body["final_esi"] in [2, 3, 4, 5]
        assert body["confidence_score"] is not None
        assert set(body["probabilities"]) == {"ESI_3", "ESI_4", "ESI_5"}
        assert body["final_source"] in ["model", "safety_rule_override"]
        assert "Model inference is not connected yet" not in body["recommendation"]
        assert body["probability_note"] == (
            "Raw model probabilities are not calibrated probabilities."
        )
    else:
        assert body["is_placeholder"] is True
        assert body["predicted_esi"] is None
        assert body["final_esi"] is None
        assert body["confidence_score"] is None
        assert body["probabilities"] == {}
    assert "not a diagnosis" in body["disclaimer"]


def test_predict_rejects_invalid_intake() -> None:
    response = client.post(
        "/predict",
        json={"patient_age": 121, "chief_complaint": "No"},
    )

    assert response.status_code == 422
