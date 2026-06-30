from fastapi import APIRouter

from app.backend.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary() -> DashboardSummaryResponse:
    return DashboardSummaryResponse(
        total_assessments=0,
        pending_reviews=0,
        completed_reviews=0,
        high_risk_flags=0,
        esi_distribution={},
        recent_assessments=[],
        is_placeholder=True,
    )
