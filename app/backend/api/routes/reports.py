from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.backend.core.config import settings
from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.report import ReportRequest, ReportResponse
from app.backend.services.pdf_service import (
    generate_assessment_report_pdf,
    report_file_name,
    report_file_path,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    report: ReportRequest,
    db: Session = Depends(get_db),
) -> ReportResponse:
    assessment = repositories.get_assessment_by_id(db, report.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    report_record = repositories.create_report_record(db, report)
    latest_prediction = repositories.get_latest_prediction_for_assessment(
        db,
        report.assessment_id,
    )
    latest_review = repositories.get_latest_clinician_review_for_assessment(
        db,
        report.assessment_id,
    )
    audit_logs = repositories.list_audit_logs_for_assessment(db, report.assessment_id)
    pdf_path = generate_assessment_report_pdf(
        assessment=assessment,
        prediction=latest_prediction,
        clinician_review=latest_review,
        audit_logs=audit_logs,
        report_id=report_record.id,
        output_dir=settings.REPORT_OUTPUT_DIR,
        include_audit=report.include_audit,
    )
    download_url = f"/reports/{report_record.id}/download"
    updated_report = repositories.update_report_record(
        db,
        report_id=report_record.id,
        report_status="generated",
        download_url=download_url,
    )
    report_record = updated_report or report_record
    repositories.create_audit_log(
        db=db,
        assessment_id=report.assessment_id,
        actor_id=None,
        action="report_generated",
        details={
            "report_id": report_record.id,
            "report_status": report_record.report_status,
            "include_audit": report.include_audit,
            "download_url": report_record.download_url,
        },
    )

    return ReportResponse(
        report_id=report_record.id,
        assessment_id=report.assessment_id,
        file_name=pdf_path.name,
        file_path=str(pdf_path),
        status=report_record.report_status,
        report_status=report_record.report_status,
        download_url=report_record.download_url,
        created_at=report_record.created_at,
        message="PDF report generated for assessment decision-support review.",
        is_placeholder=False,
    )


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    report_record = repositories.get_report_by_id(db, report_id)
    if report_record is None:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_path = report_file_path(settings.REPORT_OUTPUT_DIR, report_id)
    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=pdf_path,
        filename=report_file_name(report_id),
        media_type="application/pdf",
    )


def get_or_generate_assessment_report_pdf(
    assessment_id: str,
    db: Session,
) -> FileResponse:
    assessment = repositories.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    report_record = repositories.get_latest_generated_report_for_assessment(
        db,
        assessment_id,
    )
    if report_record is not None:
        pdf_path = report_file_path(settings.REPORT_OUTPUT_DIR, report_record.id)
        if pdf_path.exists() and pdf_path.is_file():
            return FileResponse(
                path=pdf_path,
                filename=report_file_name(report_record.id),
                media_type="application/pdf",
            )
    else:
        report_record = repositories.create_report_record(
            db,
            ReportRequest(assessment_id=assessment_id, include_audit=True),
        )

    latest_prediction = repositories.get_latest_prediction_for_assessment(db, assessment_id)
    latest_review = repositories.get_latest_clinician_review_for_assessment(db, assessment_id)
    audit_logs = repositories.list_audit_logs_for_assessment(db, assessment_id)
    pdf_path = generate_assessment_report_pdf(
        assessment=assessment,
        prediction=latest_prediction,
        clinician_review=latest_review,
        audit_logs=audit_logs,
        report_id=report_record.id,
        output_dir=settings.REPORT_OUTPUT_DIR,
        include_audit=True,
    )
    action = "report_regenerated" if report_record.report_status == "generated" else "report_generated"
    message = (
        "PDF report regenerated."
        if action == "report_regenerated"
        else "PDF report generated."
    )
    repositories.update_report_record(
        db,
        report_id=report_record.id,
        report_status="generated",
        download_url=f"/reports/{report_record.id}/download",
    )
    repositories.create_audit_log(
        db=db,
        assessment_id=assessment_id,
        actor_id=None,
        action=action,
        details={
            "report_id": report_record.id,
            "report_status": "generated",
            "download_url": f"/reports/{report_record.id}/download",
            "message": message,
        },
    )

    return FileResponse(
        path=pdf_path,
        filename=report_file_name(report_record.id),
        media_type="application/pdf",
    )
