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
    assert response.json() == {
        "total_assessments": 0,
        "pending_reviews": 0,
        "completed_reviews": 0,
        "high_risk_flags": 0,
        "esi_distribution": {},
        "recent_assessments": [],
        "is_placeholder": False,
    }


def test_dashboard_summary_counts_created_assessment() -> None:
    client.post("/assessments", json=valid_intake_payload())

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assessments"] == 1
    assert body["pending_reviews"] == 1
    assert body["completed_reviews"] == 0
    assert body["recent_assessments"][0]["chief_complaint"] == "Chest discomfort"
