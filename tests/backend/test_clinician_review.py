from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def test_clinician_review_returns_placeholder_response() -> None:
    response = client.post(
        "/clinician-review",
        json={
            "assessment_id": "assessment-123",
            "clinician_id": "clinician-456",
            "action": "accept",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"] == "assessment-123"
    assert body["status"] == "recorded_placeholder"
    assert body["is_placeholder"] is True
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
