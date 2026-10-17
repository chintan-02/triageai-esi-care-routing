from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.backend.api.main import app
from app.backend.core.config import settings
from app.backend.core.security import create_session
from app.backend.db.models import Assessment, AuditLog, AuthSession, Patient, Prediction, RateBucket, Report, User
from app.backend.db.session import SessionLocal
from app.backend.services.demo_cleanup import cleanup_demo_data
from app.backend.services.report_storage import LocalReportStore

pytestmark = pytest.mark.security
NOW = datetime.now(timezone.utc)
OLD = NOW - timedelta(days=3)


def expired_workspace(monkeypatch, tmp_path, reports=1):
    monkeypatch.setattr(settings, "REPORT_OUTPUT_DIR", str(tmp_path))
    client = TestClient(app)
    session = client.post("/api/v1/auth/demo").json()
    client.headers["Authorization"] = f"Bearer {session['access_token']}"
    aid = client.post("/predict", json={"patient_age": 40, "chief_complaint": "Synthetic ankle pain"}).json()["assessment_id"]
    for _ in range(reports):
        assert client.post("/reports/generate", json={"assessment_id": aid}).status_code == 200
    with SessionLocal() as db:
        db.execute(update(User).where(User.id == session["user"]["id"]).values(updated_at=OLD))
        db.execute(update(AuthSession).where(AuthSession.user_id == session["user"]["id"]).values(expires_at=OLD))
        db.commit()
    return session["user"]["id"], aid


def test_dry_run_is_read_only_and_apply_preserves_active_admin_and_non_demo(monkeypatch, tmp_path):
    uid, aid = expired_workspace(monkeypatch, tmp_path)
    with SessionLocal() as db:
        active = User(full_name="Active demo", role="Doctor", is_demo=True, updated_at=OLD)
        admin = User(full_name="Admin", role="Admin", is_demo=True, updated_at=OLD)
        legacy = User(full_name="Legacy", role="Doctor", is_demo=False, updated_at=OLD)
        recent = User(full_name="Recent", role="Doctor", is_demo=True)
        db.add_all([active, admin, legacy, recent]); db.flush()
        kept_ids = [active.id, admin.id, legacy.id, recent.id]
        db.add(AuthSession(token_hash="active-session", user_id=active.id, expires_at=NOW + timedelta(hours=1)))
        db.add(RateBucket(key="expired-bucket", count=1, expires_at=int(OLD.timestamp())))
        db.commit()
        session_count = db.scalar(select(func.count()).select_from(AuthSession))
        dry = cleanup_demo_data(db, now=NOW)
        assert dry["dry_run"] is True and dry["eligible_workspaces"] == 1
        assert len(list(tmp_path.glob("*.pdf"))) == 1
        assert db.get(User, uid).cleanup_pending is False
        assert db.scalar(select(func.count()).select_from(AuthSession)) == session_count
        result = cleanup_demo_data(db, apply=True, now=NOW)
        assert result["deleted_workspaces"] == 1
        assert result["deleted_report_objects"] == 1
        assert result["failed_workspaces"] == 0
        assert db.get(User, uid) is None
        assert all(db.get(User, kept) is not None for kept in kept_ids)
        assert db.get(AuthSession, "active-session") is not None
        assert db.get(RateBucket, "expired-bucket") is None
        for model in [Assessment, Patient, Prediction, Report, AuditLog]:
            assert db.scalar(select(func.count()).select_from(model)) == 0
        assert list(tmp_path.glob("*.pdf")) == []
        assert cleanup_demo_data(db, apply=True, now=NOW)["deleted_workspaces"] == 0


def test_storage_failure_retains_metadata_and_retry_completes(monkeypatch, tmp_path):
    uid, aid = expired_workspace(monkeypatch, tmp_path, reports=2)
    local = LocalReportStore(str(tmp_path))
    class FailSecondDelete:
        count = 0
        def delete(self, key):
            self.count += 1
            if self.count == 2:
                raise RuntimeError("private-storage-error")
            local.delete(key)
    failing = FailSecondDelete()
    with SessionLocal() as db:
        result = cleanup_demo_data(db, apply=True, now=NOW, store_factory=lambda _: failing)
        assert result["failed_workspaces"] == 1
        assert db.get(User, uid).cleanup_pending is True
        assert db.get(Assessment, aid) is not None
        assert db.scalar(select(func.count()).select_from(Report)) == 2
        assert len(list(tmp_path.glob("*.pdf"))) == 1
        with pytest.raises(HTTPException) as error:
            create_session(db, db.get(User, uid))
        assert error.value.status_code == 401
        result = cleanup_demo_data(db, apply=True, now=NOW, store_factory=lambda _: local)
        assert result["deleted_workspaces"] == 1
        assert db.get(User, uid) is None
        assert list(tmp_path.glob("*.pdf")) == []


def test_cleanup_keeps_a_patient_referenced_by_another_assessment(monkeypatch, tmp_path):
    uid, aid = expired_workspace(monkeypatch, tmp_path)
    with SessionLocal() as db:
        patient_id = db.get(Assessment, aid).patient_id
        other = Assessment(patient_id=patient_id, chief_complaint="Other synthetic assessment", owner_id=None)
        db.add(other); db.commit()
        other_id = other.id
        assert cleanup_demo_data(db, apply=True, now=NOW)["deleted_workspaces"] == 1
        assert db.get(Patient, patient_id) is not None
        assert db.get(Assessment, other_id) is not None


def test_pending_workspaces_refuse_authenticated_access(monkeypatch, tmp_path):
    uid, _ = expired_workspace(monkeypatch, tmp_path)
    with SessionLocal() as db:
        db.execute(update(User).where(User.id == uid).values(cleanup_pending=True))
        db.add(AuthSession(token_hash=__import__('hashlib').sha256(b"pending-token").hexdigest(),
                           user_id=uid, expires_at=NOW + timedelta(hours=1)))
        db.commit()
    client = TestClient(app, headers={"Authorization": "Bearer pending-token"})
    assert client.get("/assessments").status_code == 401


def test_cleanup_rejects_unbounded_batch_and_naive_clock():
    with SessionLocal() as db:
        for batch_size in [0, -1, settings.CLEANUP_BATCH_SIZE + 1]:
            with pytest.raises(ValueError):
                cleanup_demo_data(db, batch_size=batch_size)
        with pytest.raises(ValueError):
            cleanup_demo_data(db, now=datetime(2026, 1, 1))
