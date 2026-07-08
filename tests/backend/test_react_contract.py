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


def test_list_assessments_returns_react_contract_shape() -> None:
    client.post("/assessments", json=valid_intake_payload())

    response = client.get("/assessments")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body
    first_record = body[0]
    assert first_record["assessment_id"]
    assert first_record["patient_name"] == "Unknown patient"
    assert first_record["mrn"] == "N/A"
    assert first_record["review_status"] in {"pending", "accepted", "overridden"}
    assert first_record["review_status_normalized"] in {"pending", "accepted", "overridden"}


def test_assessment_audit_endpoint_returns_events() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.get(f"/assessments/{assessment_id}/audit")

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == assessment_id
    assert body["events"][0]["action"] == "assessment_created"
    assert body["events"][0]["event_type"] == "assessment_created"
    assert body["events"][0]["timestamp"]


def test_clinician_review_response_contains_normalized_status_and_audit_flag() -> None:
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
    assert body["review_status_normalized"] == "accepted"
    assert body["review_status"] == "accepted"
    assert body["review_status_raw"] == "review_completed"
    assert body["reviewer"] == "clinician-456"
    assert body["reviewed_at"]
    assert body["audit_event_created"] is True


def test_ready_response_contains_react_status_fields() -> None:
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    body = response.json()
    assert "database_connected" in body
    assert "model_loaded" in body
    assert "model_version" in body
    assert "is_placeholder" in body
    assert "timestamp" in body


def test_assessment_report_pdf_shortcut_returns_pdf() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.get(f"/assessments/{assessment_id}/report/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
