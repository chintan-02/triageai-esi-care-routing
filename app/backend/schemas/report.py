"""Report generation placeholder schemas."""

from datetime import datetime

from pydantic import BaseModel


class ReportRequest(BaseModel):
    assessment_id: str
    include_audit: bool = True


class ReportResponse(BaseModel):
    report_id: str | None = None
    assessment_id: str
    report_status: str
    download_url: str | None = None
    created_at: datetime | None = None
    message: str
    is_placeholder: bool
