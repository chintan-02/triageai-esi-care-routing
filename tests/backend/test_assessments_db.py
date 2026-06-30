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
    assert body["is_placeholder"] is False


def test_get_unknown_assessment_returns_404() -> None:
    response = client.get("/assessments/unknown-assessment")

    assert response.status_code == 404
