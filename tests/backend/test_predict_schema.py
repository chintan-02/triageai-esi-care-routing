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


def test_predict_returns_contract_only_placeholder() -> None:
    response = client.post("/predict", json=valid_intake_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["acuity_scale"] == "ESI"
    assert body["model_loaded"] is False
    assert body["predicted_esi"] is None
    assert body["final_esi"] is None
    assert body["confidence_score"] is None
    assert body["probabilities"] == {}
    assert body["safety_rules_triggered"] == []
    assert body["is_placeholder"] is True
    assert body["recommendation"] == (
        "Model inference is not connected yet. This endpoint validates the "
        "request contract only."
    )
    assert "not a diagnosis" in body["disclaimer"]


def test_predict_rejects_invalid_intake() -> None:
    response = client.post(
        "/predict",
        json={"patient_age": 121, "chief_complaint": "No"},
    )

    assert response.status_code == 422
