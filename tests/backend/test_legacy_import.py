import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.backend.db.base import Base
from app.backend.db.models import Assessment, AuditLog, ClinicianReview, Patient, Prediction, Report, User
from app.backend.db.session import SessionLocal
from app.backend.services.legacy_import import import_legacy_metadata

pytestmark = pytest.mark.security
OLD = datetime(2026, 7, 1, tzinfo=timezone.utc)


def source_and_owner(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    engine = create_engine('sqlite:///' + str(path))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Patient(id='patient-old', age=42, name='Synthetic patient', created_at=OLD, updated_at=OLD)); db.flush()
        db.add(Assessment(id='assessment-old', patient_id='patient-old', chief_complaint='Synthetic complaint', created_at=OLD, updated_at=OLD)); db.flush()
        db.add(Prediction(id='prediction-old', assessment_id='assessment-old', model_version='historical-model', predicted_esi=4,
                          final_source='model', recommendation='historical recommendation', explanation='historical explanation',
                          clinician_summary='historical summary', created_at=OLD))
        db.add(ClinicianReview(id='review-old', assessment_id='assessment-old', clinician_id='legacy-actor', action='accept', created_at=OLD))
        db.add(Report(id='report-old', assessment_id='assessment-old', report_status='generated', download_url='https://example.invalid/old.pdf', created_at=OLD))
        db.add(AuditLog(id='audit-old', assessment_id='assessment-old', actor_id='legacy-actor', action='historical-action', created_at=OLD))
        db.add(User(id='source-user', email='never-import@example.com', password_hash='never-import-this', role='Admin'))
        db.commit()
    engine.dispose()
    # Exercise missing nullable fields and added ownership/storage columns from old schemas.
    import sqlite3
    with sqlite3.connect(path) as db:
        for table, columns in [('assessments', ['owner_id', 'risk_flags_json', 'comorbidities_json']),
                               ('reports', ['storage_key', 'storage_backend'])]:
            kept = [row[1] for row in db.execute(f'PRAGMA table_info({table})') if row[1] not in columns]
            selected = ', '.join(kept)
            db.execute(f'CREATE TABLE old_{table} AS SELECT {selected} FROM {table}')
            db.execute(f'DROP TABLE {table}')
            db.execute(f'ALTER TABLE old_{table} RENAME TO {table}')
    with SessionLocal() as db:
        owner = User(email='owner@example.com', role='Admin', is_demo=False)
        db.add(owner); db.commit(); uid = owner.id
    return path, uid


def test_dry_run_apply_preserves_history_and_retry_is_noop(tmp_path):
    path, uid = source_and_owner(tmp_path)
    with SessionLocal() as db:
        dry = import_legacy_metadata(db, path, 'OWNER@example.com')
        assert dry['dry_run'] and dry['rows']['assessments'] == 1
        assert db.scalar(select(func.count()).select_from(Assessment)) == 0
        assert db.get(User, uid).assessment_count == 0
        result = import_legacy_metadata(db, path, 'owner@example.com', apply=True)
        assert not result['dry_run'] and result['pdf_files_restored'] == 0
        assessment = db.get(Assessment, 'assessment-old')
        assert assessment.owner_id == uid and assessment.created_at.replace(tzinfo=timezone.utc) == OLD
        prediction = db.get(Prediction, 'prediction-old')
        assert prediction.model_version == 'historical-model' and prediction.predicted_esi == 4
        assert db.get(ClinicianReview, 'review-old').clinician_id == 'legacy-actor'
        assert db.get(AuditLog, 'audit-old').actor_id == 'legacy-actor'
        report = db.get(Report, 'report-old')
        assert report.report_status == 'failed' and report.download_url is None and report.storage_key is None
        assert db.scalar(select(User).where(User.email == 'never-import@example.com')) is None
        assert (db.get(User, uid).assessment_count, db.get(User, uid).report_count, db.get(User, uid).review_count) == (1, 1, 1)
        count = db.scalar(select(func.count()).select_from(AuditLog))
        assert import_legacy_metadata(db, path, 'owner@example.com', apply=True)['already_imported']
        assert db.scalar(select(func.count()).select_from(AuditLog)) == count
        manifest = db.scalar(select(AuditLog).where(AuditLog.action == 'legacy_import_manifest'))
        assert json.loads(manifest.details_json)['original_reports'][0]['report_status'] == 'generated'


@pytest.mark.parametrize('problem', ['collision', 'orphan', 'non_admin', 'different_owner'])
def test_refusals_leave_target_unchanged(tmp_path, problem):
    path, uid = source_and_owner(tmp_path)
    if problem == 'orphan':
        import sqlite3
        with sqlite3.connect(path) as source:
            source.execute("UPDATE predictions SET assessment_id='missing'")
    with SessionLocal() as db:
        email = 'owner@example.com'
        if problem == 'collision':
            db.add(Patient(id='patient-old', age=99)); db.commit()
        elif problem == 'non_admin':
            db.get(User, uid).role = 'Doctor'; db.commit()
        elif problem == 'different_owner':
            import_legacy_metadata(db, path, email, apply=True)
            db.add(User(email='other@example.com', role='Admin', is_demo=False)); db.commit()
            email = 'other@example.com'
        before = db.scalar(select(func.count()).select_from(Assessment))
        with pytest.raises(ValueError):
            import_legacy_metadata(db, path, email, apply=True)
        db.rollback()
        assert db.scalar(select(func.count()).select_from(Assessment)) == before


def test_insert_failure_rolls_back_entire_import(tmp_path, monkeypatch):
    path, uid = source_and_owner(tmp_path)
    with SessionLocal() as db:
        original = db.flush
        calls = 0
        def fail_late(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise RuntimeError('simulated failure')
            return original(*args, **kwargs)
        monkeypatch.setattr(db, 'flush', fail_late)
        with pytest.raises(RuntimeError):
            import_legacy_metadata(db, path, 'owner@example.com', apply=True)
        db.rollback()
        monkeypatch.setattr(db, 'flush', original)
        assert db.scalar(select(func.count()).select_from(Patient)) == 0
        assert db.scalar(select(func.count()).select_from(Assessment)) == 0
        assert db.get(User, uid).assessment_count == 0
