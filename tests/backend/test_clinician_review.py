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
    assert body["clinician_decision"] == "accept"
    assert body["reviewed"] is True


def test_clinician_review_audit_details_are_clean() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "accept",
            "notes": "Reviewed by clinician.",
        },
    )
    assert response.status_code == 200

    detail_response = client.get(f"/assessments/{assessment_id}")
    review_event = next(
        event
        for event in detail_response.json()["audit_trail"]
        if event["action"] == "clinician_review_accept"
    )

    assert review_event["message"] == "Clinician accepted final routing decision."
    assert review_event["details"]["clinician_decision"] == "accept"
    assert review_event["details"]["clinician_id"] == "clinician-456"
    assert review_event["details"]["review_note"] == "Reviewed by clinician."
    assert "payload" not in review_event["details"]


def test_clinician_review_note_spacing_is_cleaned() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "accept",
            "notes": "Currentfinal routing decision accepted.",
        },
    )

    assert response.status_code == 200
    assert response.json()["review_note"] == "Current final routing decision accepted."

    detail_response = client.get(f"/assessments/{assessment_id}")
    review_event = next(
        event
        for event in detail_response.json()["audit_trail"]
        if event["action"] == "clinician_review_accept"
    )
    assert review_event["details"]["review_note"] == (
        "Current final routing decision accepted."
    )


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


def test_clinician_review_override_saves_final_esi_and_note() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-456",
            "action": "override",
            "final_esi": 2,
            "override_reason": "Vitals require higher-priority review.",
            "notes": "Escalated after clinician review.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == assessment_id
    assert body["clinician_decision"] == "override"
    assert body["clinician_final_esi"] == 2
    assert body["review_note"] == "Vitals require higher-priority review."
    assert body["status"] == "review_completed"
    assert body["is_placeholder"] is False
    assert body["timestamp"]


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
