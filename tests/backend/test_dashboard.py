from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def test_dashboard_summary_returns_zeroed_placeholder() -> None:
    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_assessments": 0,
        "pending_reviews": 0,
        "completed_reviews": 0,
        "high_risk_flags": 0,
        "esi_distribution": {},
        "recent_assessments": [],
        "is_placeholder": True,
    }
