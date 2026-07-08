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


def identified_intake_payload() -> dict[str, object]:
    return {
        **valid_intake_payload(),
        "patient_name": "Alex Morgan",
        "mrn": "MRN-4242",
        "sex": "female",
    }


def test_patient_intake_schema_validates_bounds() -> None:
    intake = PatientIntakeRequest(**identified_intake_payload())

    assert intake.patient_age == 42
    assert intake.patient_name == "Alex Morgan"
    assert intake.mrn == "MRN-4242"
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
    response_text = " ".join(
        str(body.get(field) or "")
        for field in ("explanation", "clinician_summary", "recommendation")
    )
    assert "ESIis" not in response_text
    assert "modelprobability" not in response_text
    assert "Currentfinal" not in response_text


def test_predict_persists_patient_identity() -> None:
    predict_response = client.post("/predict", json=identified_intake_payload())
    assert predict_response.status_code == 200
    assessment_id = predict_response.json()["assessment_id"]

    detail_response = client.get(f"/assessments/{assessment_id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["patient_name"] == "Alex Morgan"
    assert detail_body["mrn"] == "MRN-4242"

    list_response = client.get("/assessments")
    assert list_response.status_code == 200
    list_body = list_response.json()
    matching = next(
        item for item in list_body if item["assessment_id"] == assessment_id
    )
    assert matching["patient_name"] == "Alex Morgan"
    assert matching["mrn"] == "MRN-4242"


def test_predict_rejects_invalid_intake() -> None:
    response = client.post(
        "/predict",
        json={"patient_age": 121, "chief_complaint": "No"},
    )

    assert response.status_code == 422
