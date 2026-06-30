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


def test_clinician_review_returns_db_backed_response() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "accept",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == assessment_id
    assert body["status"] == "review_completed"
    assert body["is_placeholder"] is False
    assert body["review_id"]


def test_clinician_review_override_requires_reason() -> None:
    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": "assessment-123",
            "clinician_id": "clinician-456",
            "action": "override",
            "final_esi": 2,
        },
    )

    assert response.status_code == 422


def test_clinician_review_for_unknown_assessment_returns_404() -> None:
    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": "unknown-assessment",
            "clinician_id": "clinician-456",
            "action": "accept",
        },
    )

    assert response.status_code == 404
