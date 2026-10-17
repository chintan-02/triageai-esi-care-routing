"""Bounded, retryable demo retention. No database rows disappear before their objects."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.db.models import (
    Assessment, AuditLog, AuthSession, ClinicianReview, Patient, Prediction,
    RateBucket, Report, User,
)
from app.backend.services.pdf_service import report_file_name
from app.backend.services.report_storage import get_report_store


def _eligible(now: datetime):
    active_session = exists(select(AuthSession.token_hash).where(
        AuthSession.user_id == User.id, AuthSession.expires_at > now,
    ))
    return (
        User.is_demo.is_(True), User.role != "Admin", ~active_session,
        User.updated_at < now - timedelta(hours=settings.DEMO_RETENTION_HOURS),
    )


def _delete_workspace(db: Session, user_id: str, now: datetime, store_factory) -> int | None:
    # UPDATE obtains a row lock on PostgreSQL (and a write lock on SQLite).
    # Recheck eligibility under that lock; concurrent cleanups cannot delete
    # active/newly-touched workspaces. It stays held through object deletion.
    claimed = db.scalar(update(User).where(User.id == user_id, *_eligible(now))
                        .values(cleanup_pending=True, updated_at=User.updated_at).returning(User.id))
    if claimed is None:
        db.rollback()
        return None
    assessments = list(db.scalars(select(Assessment).where(Assessment.owner_id == user_id)))
    assessment_ids = [item.id for item in assessments]
    patient_ids = [item.patient_id for item in assessments]
    reports = list(db.scalars(select(Report).where(Report.assessment_id.in_(assessment_ids))))
    for report in reports:
        # Queued/failed uploads also have deterministic keys and a stored backend.
        store_factory(report.storage_backend or "local").delete(
            report.storage_key or report_file_name(report.id)
        )
    for model in [AuditLog, ClinicianReview, Prediction, Report]:
        db.execute(delete(model).where(model.assessment_id.in_(assessment_ids)))
    db.execute(delete(Assessment).where(Assessment.owner_id == user_id))
    db.execute(delete(Patient).where(
        Patient.id.in_(patient_ids),
        ~exists(select(Assessment.id).where(Assessment.patient_id == Patient.id)),
    ))
    db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
    db.execute(delete(User).where(User.id == user_id))
    db.commit()
    return len(reports)


def cleanup_demo_data(db: Session, *, apply: bool = False, now: datetime | None = None,
                      batch_size: int | None = None, store_factory=None) -> dict[str, int | bool]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Cleanup requires an explicit timezone-aware clock")
    batch_size = settings.CLEANUP_BATCH_SIZE if batch_size is None else batch_size
    if not 1 <= batch_size <= settings.CLEANUP_BATCH_SIZE:
        raise ValueError("Batch size exceeds the configured cleanup bound")
    store_factory = store_factory or get_report_store
    user_ids = list(db.scalars(select(User.id).where(*_eligible(now))
                              .order_by(User.updated_at, User.id).limit(batch_size)))
    session_keys = list(db.scalars(select(AuthSession.token_hash).where(
        AuthSession.expires_at <= now).order_by(AuthSession.expires_at).limit(batch_size)))
    bucket_keys = list(db.scalars(select(RateBucket.key).where(
        RateBucket.expires_at <= int(now.timestamp())).order_by(RateBucket.expires_at).limit(batch_size)))
    summary = {"dry_run": not apply, "eligible_workspaces": len(user_ids),
               "expired_sessions": len(session_keys), "expired_rate_buckets": len(bucket_keys),
               "deleted_workspaces": 0, "deleted_report_objects": 0, "failed_workspaces": 0}
    if not apply:
        return summary
    db.rollback()  # End the discovery read transaction before independent claims.
    for user_id in user_ids:
        # Commit a tombstone before external I/O. Failed deletion is retryable,
        # while authentication and login refuse a workspace awaiting cleanup.
        marked = db.scalar(update(User).where(User.id == user_id, *_eligible(now))
                           .values(cleanup_pending=True, updated_at=User.updated_at).returning(User.id))
        db.commit()
        if marked is None:
            continue
        try:
            deleted = _delete_workspace(db, user_id, now, store_factory)
            if deleted is not None:
                summary["deleted_workspaces"] += 1
                summary["deleted_report_objects"] += deleted
        except Exception:
            db.rollback()
            summary["failed_workspaces"] += 1
    # Only preselected expired rows may be purged; active sessions are never removed.
    db.execute(delete(AuthSession).where(AuthSession.token_hash.in_(session_keys), AuthSession.expires_at <= now))
    db.execute(delete(RateBucket).where(RateBucket.key.in_(bucket_keys), RateBucket.expires_at <= int(now.timestamp())))
    db.commit()
    return summary
