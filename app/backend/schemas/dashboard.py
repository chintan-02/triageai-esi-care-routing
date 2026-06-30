"""Dashboard summary schemas."""

from typing import Any

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_assessments: int
    pending_reviews: int
    completed_reviews: int
    high_risk_flags: int
    esi_distribution: dict[str, int]
    recent_assessments: list[Any]
    is_placeholder: bool
