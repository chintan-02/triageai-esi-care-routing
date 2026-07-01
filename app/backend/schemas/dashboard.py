"""Dashboard summary schemas."""

from datetime import datetime

from pydantic import BaseModel


class RecentAssessmentItem(BaseModel):
    assessment_id: str
    patient_id: str
    patient_age: int | None = None
    sex: str | None = None
    chief_complaint: str
    status: str
    created_at: datetime
    predicted_esi: int | None = None
    model_final_esi: int | None = None
    final_esi: int | None = None
    clinician_final_esi: int | None = None
    clinician_decision: str | None = None
    final_source: str | None = None
    confidence_score: float | None = None


class DashboardSummaryResponse(BaseModel):
    total_assessments: int
    model_predictions_generated: int = 0
    reviewed_assessments: int = 0
    pending_reviews: int
    completed_reviews: int
    override_count: int = 0
    most_common_final_esi: int | None = None
    high_risk_flags: int
    esi_distribution: dict[str, int]
    recent_assessments: list[RecentAssessmentItem]
    is_placeholder: bool
