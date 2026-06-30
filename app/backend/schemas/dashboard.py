"""Dashboard summary schemas."""

from datetime import datetime

from pydantic import BaseModel


class RecentAssessmentItem(BaseModel):
    assessment_id: str
    patient_id: str
    chief_complaint: str
    status: str
    created_at: datetime
    final_esi: int | None = None


class DashboardSummaryResponse(BaseModel):
    total_assessments: int
    pending_reviews: int
    completed_reviews: int
    high_risk_flags: int
    esi_distribution: dict[str, int]
    recent_assessments: list[RecentAssessmentItem]
    is_placeholder: bool
