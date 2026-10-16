"""Exercise real API authentication, never the legacy contract override."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.backend.api.main import app
from app.backend.core.config import settings
from app.backend.db.models import AuthSession, User
from app.backend.db.session import SessionLocal

pytestmark = pytest.mark.security
INTAKE = {"patient_age": 42, "chief_complaint": "Synthetic ankle injury", "oxygen_saturation": 98}


def visitor():
    client = TestClient(app)
    response = client.post("/api/v1/auth/demo")
    assert response.status_code == 200
    payload = response.json()
    client.headers["Authorization"] = f"Bearer {payload['access_token']}"
    return client, payload


@pytest.mark.parametrize("method,path,payload", [
    ("get", "/assessments", None),
    ("get", "/dashboard/summary", None),
    ("post", "/predict", INTAKE),
    ("get", "/reports/fake/download", None),
    ("post", "/nlp/extract-intake", {"note_text": "Synthetic note"}),
    ("post", "/speech/transcribe", None),
])
def test_protected_endpoints_require_session(method, path, payload):
    response = TestClient(app).request(method, path, json=payload)
    assert response.status_code == 401


def test_private_end_to_end_inference_review_report_and_dashboard():
    alice, alice_session = visitor()
    bob, _ = visitor()
    response = alice.post("/predict", json=INTAKE)
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["model_loaded"] is True
    assert prediction["is_placeholder"] is False
    aid = prediction["assessment_id"]
    assert len(alice.get("/assessments").json()) == 1
    assert bob.get("/assessments").json() == []
    assert bob.get("/dashboard/summary").json()["total_assessments"] == 0
    assert bob.get("/dashboard/summary").json()["model_predictions_generated"] == 0
    assert bob.get("/dashboard/summary").json()["recent_assessments"] == []
    for suffix in ["", "/audit", "/report/pdf"]:
        assert bob.get(f"/assessments/{aid}{suffix}").status_code == 404
    review = {"assessment_id": aid, "action": "accept", "clinician_id": "forged-admin", "reviewer_role": "Admin"}
    assert bob.post("/clinician-review", json=review).status_code == 404
    accepted = alice.post("/clinician-review", json=review)
    assert accepted.status_code == 200
    assert accepted.json()["reviewer"] == alice_session["user"]["id"]
    assert accepted.json()["reviewer_role"] == "Doctor"
    assert alice.get("/dashboard/summary").json()["completed_reviews"] == 1
    assert bob.get("/dashboard/summary").json()["completed_reviews"] == 0
    assert bob.post("/reports/generate", json={"assessment_id": aid}).status_code == 404
    generated = alice.post("/reports/generate", json={"assessment_id": aid})
    assert generated.status_code == 200
    current = alice.get("/assessments").json()[0]
    assert current["reports"][0]["report_id"] == generated.json()["report_id"]
    assert current["reports"][0]["report_status"] == "generated"
    assert bob.get("/assessments").json() == []
    url = generated.json()["download_url"]
    assert bob.get(url).status_code == 404
    pdf = alice.get(url)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert pdf.headers["cache-control"] == "no-store"


def test_logout_revokes_token_and_expiry_is_enforced():
    client, session = visitor()
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client, session = visitor()
    with SessionLocal() as db:
        record = db.scalar(select(AuthSession).where(AuthSession.user_id == session["user"]["id"]))
        record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get("/assessments").status_code == 401


def test_register_login_password_hash_and_no_admin_self_assignment():
    client = TestClient(app)
    payload = {"name": "Example", "email": "Example@example.test", "password": "a-long-test-password", "role": "Admin"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    session = response.json()
    assert session["user"]["role"] == "Doctor"
    with SessionLocal() as db:
        user = db.get(User, session["user"]["id"])
        assert user.password_hash != payload["password"]
        assert db.get(AuthSession, session["access_token"]) is None
        assert db.scalar(select(AuthSession)).token_hash != session["access_token"]
    response = client.post("/api/v1/auth/login", json={"identifier": "example@example.test", "password": payload["password"], "role": "Admin"})
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "Doctor"
    assert client.post("/api/v1/auth/login", json={"identifier": "example@example.test", "password": "wrong"}).status_code == 401
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    assert client.post("/api/v1/auth/register", json={**payload, "password": "short"}).status_code == 422


def test_demo_can_be_disabled(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_DEMO_ENABLED", False)
    client = TestClient(app)
    assert client.post("/api/v1/auth/demo").status_code == 403
    assert client.post("/api/v1/auth/register", json={"name": "Test", "email": "t@example.test", "password": "long-test-password"}).status_code == 403


def test_invalid_token_is_rejected():
    client = TestClient(app, headers={"Authorization": "Bearer fabricated"})
    assert client.get("/assessments").status_code == 401


def test_review_permission_is_enforced_from_database_role():
    client, session = visitor()
    aid = client.post("/predict", json=INTAKE).json()["assessment_id"]
    with SessionLocal() as db:
        user = db.get(User, session["user"]["id"])
        user.role = "Nurse"
        db.commit()
    override = {"assessment_id": aid, "action": "override", "final_esi": 2,
                "override_reason": "Synthetic review", "reviewer_role": "Doctor"}
    assert client.post("/clinician-review", json=override).status_code == 403
    with SessionLocal() as db:
        user = db.get(User, session["user"]["id"])
        user.role = "Admin"
        db.commit()
    assert client.post("/clinician-review", json={"assessment_id": aid, "action": "accept"}).status_code == 403
