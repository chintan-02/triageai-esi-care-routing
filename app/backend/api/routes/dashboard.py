from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**repositories.get_dashboard_summary(db))
