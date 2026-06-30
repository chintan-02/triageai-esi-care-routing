"""Report generation placeholder schemas."""

from pydantic import BaseModel


class ReportRequest(BaseModel):
    assessment_id: str
    include_audit: bool = True


class ReportResponse(BaseModel):
    assessment_id: str
    report_status: str
    download_url: str | None = None
    message: str
    is_placeholder: bool
