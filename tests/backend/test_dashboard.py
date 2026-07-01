from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def valid_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "chief_complaint": "Chest discomfort",
        "pain_score": 6,
        "oxygen_saturation": 98.0,
    }


def test_dashboard_summary_returns_zeroed_db_summary() -> None:
    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assessments"] == 0
    assert body["model_predictions_generated"] == 0
    assert body["reviewed_assessments"] == 0
    assert body["pending_reviews"] == 0
    assert body["completed_reviews"] == 0
    assert body["override_count"] == 0
    assert body["most_common_final_esi"] is None
    assert body["high_risk_flags"] == 0
    assert body["esi_distribution"] == {}
    assert body["recent_assessments"] == []
    assert body["is_placeholder"] is False


def test_dashboard_summary_counts_created_assessment() -> None:
    client.post("/assessments", json=valid_intake_payload())

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assessments"] == 1
    assert body["pending_reviews"] == 1
    assert body["completed_reviews"] == 0
    assert body["recent_assessments"][0]["chief_complaint"] == "Chest discomfort"
    assert body["recent_assessments"][0]["patient_age"] == 42


def test_dashboard_summary_counts_predictions_and_override_review() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assessment_id = predict_response.json()["assessment_id"]

    review_response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "override",
            "final_esi": 2,
            "override_reason": "Additional bedside context requires escalation.",
        },
    )
    assert review_response.status_code == 200

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assessments"] == 1
    assert body["model_predictions_generated"] == 1
    assert body["reviewed_assessments"] == 1
    assert body["completed_reviews"] == 1
    assert body["pending_reviews"] == 0
    assert body["override_count"] == 1
    assert body["high_risk_flags"] == 1
    assert body["esi_distribution"] == {"2": 1}
    assert body["most_common_final_esi"] == 2
    recent = body["recent_assessments"][0]
    assert recent["assessment_id"] == assessment_id
    assert recent["status"] == "review_completed"
    assert recent["clinician_decision"] == "override"
    assert recent["clinician_final_esi"] == 2
    assert recent["final_source"] == "clinician_override"
