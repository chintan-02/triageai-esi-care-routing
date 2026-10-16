from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.backend.api.main import app
from app.backend.core.config import settings
from app.backend.core.limits import consume, reserve_workspace
from app.backend.db.models import Assessment, Patient, RateBucket, User
from app.backend.db.session import SessionLocal, engine

pytestmark = pytest.mark.security
INTAKE = {"patient_age": 40, "chief_complaint": "Synthetic ankle pain"}


def visitor():
    client = TestClient(app)
    response = client.post("/api/v1/auth/demo")
    assert response.status_code == 200
    payload = response.json()
    client.headers["Authorization"] = f"Bearer {payload['access_token']}"
    return client, payload["user"]["id"]


def test_atomic_shared_rate_limit_across_independent_sessions_and_engine():
    def request(_):
        with SessionLocal() as db:
            try:
                consume(db, "concurrent-test", "private-ip", 5, now=120)
                return True
            except HTTPException as exc:
                assert exc.status_code == 429
                assert exc.headers["Retry-After"] == "60"
                return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(request, range(24))) == 5
    another_engine = create_engine(engine.url)
    try:
        with Session(another_engine) as db:
            with pytest.raises(HTTPException) as error:
                consume(db, "concurrent-test", "private-ip", 5, now=121)
            assert error.value.status_code == 429
            consume(db, "concurrent-test", "private-ip", 5, now=180)
            assert all(len(key) == 64 and "private-ip" not in key for key in db.scalars(select(RateBucket.key)))
    finally:
        another_engine.dispose()


def test_limiter_fails_closed_on_database_error():
    db = Mock()
    db.get_bind.return_value.dialect.name = "sqlite"
    db.scalar.side_effect = OperationalError("statement", {}, RuntimeError("private-db-details"))
    with pytest.raises(HTTPException) as error:
        consume(db, "test", "subject", 5)
    assert error.value.status_code == 503
    assert "private-db-details" not in error.value.detail
    db.rollback.assert_called_once()


def test_issuance_limit_cannot_be_bypassed_with_forwarded_headers(monkeypatch):
    monkeypatch.setattr(settings, "SESSION_ISSUANCE_PER_HOUR", 2)
    client = TestClient(app)
    assert client.post("/api/v1/auth/demo", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.post("/api/v1/auth/demo", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200
    response = client.post("/api/v1/auth/demo", headers={"X-Forwarded-For": "3.3.3.3", "Origin": "http://localhost:5173"})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_login_account_limit_charges_failed_attempts(monkeypatch):
    monkeypatch.setattr(settings, "LOGIN_ACCOUNT_PER_HOUR", 2)
    client = TestClient(app)
    payload = {"identifier": "absent@example.test", "password": "wrong-password"}
    assert client.post("/api/v1/auth/login", json=payload).status_code == 401
    assert client.post("/api/v1/auth/login", json=payload).status_code == 401
    assert client.post("/api/v1/auth/login", json=payload).status_code == 429


def test_global_expensive_limit_is_shared_across_visitors(monkeypatch):
    monkeypatch.setattr(settings, "EXPENSIVE_GLOBAL_PER_HOUR", 1)
    first, _ = visitor()
    second, _ = visitor()
    assert first.post("/predict", json=INTAKE).status_code == 200
    assert second.post("/predict", json=INTAKE).status_code == 429
    assert second.get("/health").status_code == 200


def test_workspace_quota_covers_both_creation_paths_without_orphan_patients(monkeypatch):
    monkeypatch.setattr(settings, "MAX_WORKSPACE_ASSESSMENTS", 2)
    client, uid = visitor()
    assert client.post("/predict", json=INTAKE).status_code == 200
    assert client.post("/assessments", json=INTAKE).status_code == 200
    assert client.post("/predict", json=INTAKE).status_code == 409
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Patient)) == 2
        assert db.scalar(select(func.count()).select_from(Assessment)) == 2
        assert db.get(User, uid).assessment_count == 2


def test_quota_reservation_is_atomic_under_concurrent_writers(monkeypatch):
    monkeypatch.setattr(settings, "MAX_WORKSPACE_ASSESSMENTS", 3)
    _, uid = visitor()
    def reserve(_):
        with SessionLocal() as db:
            db.info["owner_id"] = uid
            try:
                reserve_workspace(db, "assessment")
                db.commit()
                return True
            except HTTPException as exc:
                assert exc.status_code == 409
                return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(16))) == 3
    with SessionLocal() as db:
        assert db.get(User, uid).assessment_count == 3


def test_report_and_review_quotas_preserve_existing_downloads(monkeypatch):
    monkeypatch.setattr(settings, "MAX_WORKSPACE_REPORTS", 1)
    monkeypatch.setattr(settings, "MAX_WORKSPACE_REVIEWS", 1)
    client, _ = visitor()
    aid = client.post("/predict", json=INTAKE).json()["assessment_id"]
    assert client.post("/clinician-review", json={"assessment_id": aid, "action": "accept"}).status_code == 200
    assert client.post("/clinician-review", json={"assessment_id": aid, "action": "accept"}).status_code == 409
    response = client.post("/reports/generate", json={"assessment_id": aid})
    assert response.status_code == 200
    assert client.post("/reports/generate", json={"assessment_id": aid}).status_code == 409
    assert client.get(response.json()["download_url"]).content.startswith(b"%PDF")
    assert client.get(f"/assessments/{aid}/report/pdf").content.startswith(b"%PDF")


def test_oversized_inputs_and_audio_are_rejected_before_work(monkeypatch):
    client, _ = visitor()
    assert client.post("/assessments", json={**INTAKE, "chief_complaint": "x" * 1001}).status_code == 422
    assert client.post("/assessments", json={**INTAKE, "risk_flags": ["flag"] * 33}).status_code == 422
    monkeypatch.setattr(settings, "MAX_JSON_BYTES", 1024)
    assert client.post("/assessments", content=b"x" * 1025).status_code == 413
    monkeypatch.setattr(settings, "MAX_AUDIO_BYTES", 1024)
    transcribe = Mock()
    monkeypatch.setattr("app.backend.api.routes.speech.transcribe_audio", transcribe)
    assert client.post("/speech/transcribe", files={"audio_file": ("test.wav", b"x" * 1025, "audio/wav")}).status_code == 413
    transcribe.assert_not_called()


def test_chunked_body_cap_does_not_trust_declared_length(monkeypatch):
    import asyncio
    from app.backend.core.body_limits import BodySizeLimitMiddleware
    monkeypatch.setattr(settings, "MAX_JSON_BYTES", 1024)
    called = []
    async def downstream(scope, receive, send): called.append(True)
    frames = iter([{"type": "http.request", "body": b"x" * 800, "more_body": True},
                   {"type": "http.request", "body": b"x" * 800, "more_body": False}])
    sent = []
    async def receive(): return next(frames)
    async def send(message): sent.append(message)
    asyncio.run(BodySizeLimitMiddleware(downstream)(
        {"type": "http", "path": "/predict", "headers": [(b"content-length", b"3")]}, receive, send))
    assert sent[0]["status"] == 413
    assert called == []


def test_generated_report_size_is_bounded(monkeypatch):
    monkeypatch.setattr(settings, "MAX_REPORT_BYTES", 1)
    client, _ = visitor()
    aid = client.post("/assessments", json=INTAKE).json()["assessment_id"]
    response = client.post("/reports/generate", json={"assessment_id": aid})
    assert response.status_code == 413
    assert "exceeds the allowed size" in response.json()["detail"]


def test_per_visitor_api_limit_persists_when_client_is_recreated(monkeypatch):
    monkeypatch.setattr(settings, "API_PER_MINUTE", 1)
    client, _ = visitor()
    assert client.get("/assessments").status_code == 200
    recreated = TestClient(app, headers=dict(client.headers))
    assert recreated.get("/assessments").status_code == 429
