from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.report import ReportRequest, ReportResponse

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
    return ReportResponse(
        report_id=report_record.id,
        assessment_id=report.assessment_id,
        report_status=report_record.report_status,
        download_url=None,
        created_at=report_record.created_at,
        message="Report metadata queued. No PDF file is generated yet.",
        is_placeholder=True,
    )
