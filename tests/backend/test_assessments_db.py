from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def valid_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "sex": "female",
        "chief_complaint": "Chest discomfort",
        "pain_score": 6,
        "oxygen_saturation": 98.0,
    }


def test_create_assessment_persists_record() -> None:
    response = client.post("/assessments", json=valid_intake_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"]
    assert body["patient_id"]
    assert body["status"] == "pending_review"
    assert body["created_at"]
    assert body["is_placeholder"] is False


def test_get_assessment_returns_created_record() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.get(f"/assessments/{assessment_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == assessment_id
    assert body["status"] == "pending_review"
    assert body["chief_complaint"] == "Chest discomfort"
    assert body["intake"]["patient_age"] == 42
    assert body["latest_prediction"] is None
    assert body["latest_clinician_review"] is None
    assert body["audit_trail"][0]["action"] == "assessment_created"
    assert body["is_placeholder"] is False


def test_get_assessment_returns_prediction_review_and_audit_detail() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assert predict_response.status_code == 200
    assessment_id = predict_response.json()["assessment_id"]

    review_response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "override",
            "final_esi": 2,
            "override_reason": "Additional bedside context requires escalation.",
            "notes": "Reviewed with clinician.",
        },
    )
    assert review_response.status_code == 200

    response = client.get(f"/assessments/{assessment_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == assessment_id
    assert body["status"] == "review_completed"
    assert body["latest_prediction"]["prediction_id"]
    assert body["latest_prediction"]["probabilities"] is not None
    assert body["latest_clinician_review"]["clinician_decision"] == "override"
    assert body["latest_clinician_review"]["clinician_final_esi"] == 2
    assert (
        body["latest_clinician_review"]["override_reason"]
        == "Additional bedside context requires escalation."
    )
    audit_actions = [event["action"] for event in body["audit_trail"]]
    assert "assessment_created" in audit_actions
    assert "prediction_generated" in audit_actions
    assert "clinician_review_override" in audit_actions


def test_get_unknown_assessment_returns_404() -> None:
    response = client.get("/assessments/unknown-assessment")

    assert response.status_code == 404
