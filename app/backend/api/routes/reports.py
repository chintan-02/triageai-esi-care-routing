from fastapi import APIRouter

from app.backend.schemas.report import ReportRequest, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
def generate_report(report: ReportRequest) -> ReportResponse:
    return ReportResponse(
        assessment_id=report.assessment_id,
        report_status="placeholder",
        download_url=None,
        message="Report generation contract is ready. No report file is generated yet.",
        is_placeholder=True,
    )
