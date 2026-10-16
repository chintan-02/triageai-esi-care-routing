from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.core.security import get_authenticated_db as get_db
from app.backend.db import repositories
from app.backend.schemas.report import ReportRequest, ReportResponse
from app.backend.services.pdf_service import generate_assessment_report_pdf, report_file_name
from app.backend.services.report_storage import get_report_store

router = APIRouter(prefix="/reports", tags=["reports"])


def _persist_pdf(db: Session, assessment, record, include_audit: bool) -> str | None:
    """Generate in a temporary directory, upload, then mark the DB record generated."""
    try:
        with TemporaryDirectory(prefix="triageai-report-") as temporary:
            generated = generate_assessment_report_pdf(
                assessment=assessment,
                prediction=repositories.get_latest_prediction_for_assessment(db, assessment.id),
                clinician_review=repositories.get_latest_clinician_review_for_assessment(db, assessment.id),
                audit_logs=repositories.list_audit_logs_for_assessment(db, assessment.id),
                report_id=record.id, output_dir=temporary, include_audit=include_audit,
            )
            # Keys contain only a server-generated report UUID, never a patient identifier.
            record.storage_key = report_file_name(record.id)
            record.storage_backend = settings.REPORT_STORAGE_BACKEND
            content = generated.read_bytes()
            if len(content) > settings.MAX_REPORT_BYTES:
                raise HTTPException(413, "Generated report exceeds the allowed size")
            get_report_store().put(record.storage_key, content)
        record.report_status = "generated"
        record.download_url = f"/reports/{record.id}/download"
        db.commit()
    except Exception as exc:
        db.rollback()
        record.report_status = "failed"
        db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(503, "Report storage is temporarily unavailable") from None
    if record.storage_backend == "local":
        return str(Path(settings.REPORT_OUTPUT_DIR) / record.storage_key)
    return None


def _pdf_response(record) -> Response:
    try:
        # Existing local reports predate the storage metadata migration.
        key = record.storage_key or report_file_name(record.id)
        content = get_report_store(record.storage_backend or "local").get(key)
    except FileNotFoundError:
        raise HTTPException(404, "Report file not found") from None
    except Exception:
        raise HTTPException(503, "Report storage is temporarily unavailable") from None
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{report_file_name(record.id)}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/generate", response_model=ReportResponse)
def generate_report(report: ReportRequest, db: Session = Depends(get_db)) -> ReportResponse:
    assessment = repositories.get_assessment_by_id(db, report.assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    record = repositories.create_report_record(db, report)
    file_path = _persist_pdf(db, assessment, record, report.include_audit)
    repositories.create_audit_log(
        db=db, assessment_id=assessment.id, actor_id=db.info.get("owner_id"),
        action="report_generated", details={"report_id": record.id,
            "report_status": record.report_status, "include_audit": report.include_audit,
            "download_url": record.download_url},
    )
    return ReportResponse(
        report_id=record.id, assessment_id=assessment.id, file_name=report_file_name(record.id),
        file_path=file_path, status=record.report_status, report_status=record.report_status,
        download_url=record.download_url, created_at=record.created_at,
        message="PDF report generated for assessment decision-support review.", is_placeholder=False,
    )


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)) -> Response:
    record = repositories.get_report_by_id(db, report_id)
    if record is None or record.report_status != "generated":
        raise HTTPException(404, "Report not found")
    return _pdf_response(record)


def get_or_generate_assessment_report_pdf(assessment_id: str, db: Session) -> Response:
    assessment = repositories.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    record = repositories.get_latest_generated_report_for_assessment(db, assessment_id)
    regenerated = record is not None
    if record is not None:
        try:
            return _pdf_response(record)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
    else:
        record = repositories.create_report_record(db, ReportRequest(assessment_id=assessment_id, include_audit=True))
    _persist_pdf(db, assessment, record, True)
    action = "report_regenerated" if regenerated else "report_generated"
    repositories.create_audit_log(
        db=db, assessment_id=assessment_id, actor_id=db.info.get("owner_id"), action=action,
        details={"report_id": record.id, "report_status": "generated", "download_url": record.download_url,
                 "message": "PDF report regenerated." if regenerated else "PDF report generated."},
    )
    return _pdf_response(record)
