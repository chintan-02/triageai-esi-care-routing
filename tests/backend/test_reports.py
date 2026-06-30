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


def test_generate_report_creates_metadata_record() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_id"]
    assert body["assessment_id"] == assessment_id
    assert body["report_status"] == "queued"
    assert body["download_url"] is None
    assert body["created_at"]
    assert body["is_placeholder"] is True


def test_generate_report_for_unknown_assessment_returns_404() -> None:
    response = client.post(
        "/reports/generate",
        json={"assessment_id": "unknown-assessment", "include_audit": True},
    )

    assert response.status_code == 404
