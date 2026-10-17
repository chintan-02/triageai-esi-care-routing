"""Operator-only metadata recovery from local synthetic demo SQLite snapshots.

Never imports credentials, sessions, remote URLs, or claims to restore PDF bytes.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import Boolean, DateTime, func, select, update
from sqlalchemy.orm import Session

from app.backend.db.models import (
    Assessment, AuditLog, ClinicianReview, Patient, Prediction, Report, User,
)

MODELS = (Patient, Assessment, Prediction, ClinicianReview, Report, AuditLog)


def read_snapshot(path: Path) -> tuple[dict, str]:
    path = path.resolve(strict=True)
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source:
        source.row_factory = sqlite3.Row
        source.execute('BEGIN')  # one consistent read snapshot across all tables
        data = {}
        for model in MODELS:
            table = model.__tablename__
            columns = {row[1] for row in source.execute(f'PRAGMA table_info("{table}")')}
            if not columns or 'id' not in columns:
                raise ValueError(f'Source is missing required table/ID: {table}')
            if columns - set(model.__table__.columns.keys()):
                raise ValueError(f'Unsupported source columns in {table}')
            data[table] = [dict(row) for row in source.execute(f'SELECT * FROM "{table}" ORDER BY id')]
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return data, digest


def _values(model, row):
    values = dict(row)
    for column in model.__table__.columns:
        if column.name not in values:
            if not column.nullable and column.default is None and column.server_default is None:
                raise ValueError(f'Source is missing required field: {model.__tablename__}.{column.name}')
            continue
        value = values[column.name]
        if value is None:
            if not column.nullable:
                raise ValueError(f'Source has null required field: {model.__tablename__}.{column.name}')
        elif isinstance(column.type, DateTime):
            parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
            values[column.name] = parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        elif isinstance(column.type, Boolean):
            if value not in (0, 1, False, True):
                raise ValueError('Source has invalid boolean')
            values[column.name] = bool(value)
    if not isinstance(values.get('id'), str) or not values['id']:
        raise ValueError('Source has invalid record ID')
    return values


def import_legacy_metadata(db: Session, source: Path, owner_email: str, *, apply=False) -> dict:
    """All-or-nothing DB import; repeated identical snapshots are no-ops.

    Caller owns a fresh session. Failures must roll back before reuse.
    """
    data, digest = read_snapshot(source)
    marker_id = str(uuid5(NAMESPACE_URL, 'triageai:legacy-metadata:v1:' + digest))
    owner = db.scalar(select(User).where(User.email == owner_email.strip().lower()))
    if owner is None or owner.role != 'Admin' or owner.is_demo or owner.cleanup_pending:
        raise ValueError('Target must be an existing, non-demo Admin account not pending cleanup')
    summary = dict(dry_run=not apply, source_sha256=digest, already_imported=False,
                   rows={table: len(rows) for table, rows in data.items()},
                   pdf_files_restored=0, report_metadata_only=len(data['reports']),
                   unlinked_audit_events=sum(row.get('assessment_id') is None for row in data['audit_logs']))
    marker = db.get(AuditLog, marker_id)
    if marker:
        details = json.loads(marker.details_json)
        if details['owner_id'] != owner.id:
            raise ValueError('This source was already imported into a different workspace')
        summary['already_imported'] = True
        return summary
    if apply:
        # Serialize imports/quota updates and conflict with cleanup/session touches.
        claimed = db.execute(update(User).where(
            User.id == owner.id, User.role == 'Admin', User.is_demo.is_(False),
            User.cleanup_pending.is_(False),
        ).values(updated_at=User.updated_at).returning(User.id)).scalar_one_or_none()
        if claimed is None:
            raise ValueError('Target account changed; retry after inspecting it')
        # Recheck after the lock: another importer may have committed while we waited.
        if db.get(AuditLog, marker_id, populate_existing=True):
            summary['already_imported'] = True
            return summary
    prepared = {}
    for model in MODELS:
        table = model.__tablename__
        prepared[table] = [_values(model, row) for row in data[table]]
        for row in prepared[table]:
            if db.get(model, row['id']) is not None:
                raise ValueError(f'Existing record ID conflict in {table}; no automatic merge')
    patient_ids = {row['id'] for row in prepared['patients']}
    assessment_ids = {row['id'] for row in prepared['assessments']}
    for row in prepared['assessments']:
        if row['patient_id'] not in patient_ids:
            raise ValueError('Source assessment references a missing patient')
        row['owner_id'] = owner.id
    for table in ('predictions', 'clinician_reviews', 'reports', 'audit_logs'):
        for row in prepared[table]:
            aid = row.get('assessment_id')
            if aid not in assessment_ids and not (table == 'audit_logs' and aid is None):
                raise ValueError(f'Source has an orphan assessment reference in {table}')
    for row in prepared['reports']:
        row.update(report_status='failed', download_url=None, storage_key=None, storage_backend=None)
    summary['post_import_counts'] = {}
    for model, field in ((Assessment, 'assessment_count'), (Report, 'report_count'), (ClinicianReview, 'review_count')):
        query = select(func.count()).select_from(model)
        if model is Assessment:
            query = query.where(Assessment.owner_id == owner.id)
        else:
            query = query.join(Assessment).where(Assessment.owner_id == owner.id)
        summary['post_import_counts'][field] = db.scalar(query) + len(prepared[model.__tablename__])
    if not apply:
        return summary
    for model in MODELS:
        db.add_all(model(**row) for row in prepared[model.__tablename__])
        db.flush()  # honor foreign-key order on PostgreSQL as well as SQLite
    for row in data['assessments']:
        db.add(AuditLog(
            id=str(uuid5(NAMESPACE_URL, marker_id + ':' + row['id'])),
            assessment_id=row['id'], actor_id=owner.id, action='legacy_metadata_imported',
            details_json=json.dumps({'source_sha256': digest, 'original_owner_id': row.get('owner_id'),
                                     'historical_actors_preserved': True, 'pdf_bytes_restored': False}),
        ))
    db.add(AuditLog(id=marker_id, actor_id=owner.id, action='legacy_import_manifest',
                   details_json=json.dumps({'owner_id': owner.id, 'source_sha256': digest,
                                            'original_reports': data['reports'], 'rows': summary['rows']})))
    db.execute(update(User).where(User.id == owner.id).values(**summary['post_import_counts']))
    db.commit()
    return summary
