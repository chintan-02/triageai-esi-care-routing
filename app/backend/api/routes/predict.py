from time import perf_counter

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.services.prediction_service import predict_esi_for_intake

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=ESIPredictionResponse)
def predict_esi(
    intake: PatientIntakeRequest,
    db: Session = Depends(get_db),
) -> ESIPredictionResponse:
    assessment = repositories.create_assessment(db, intake)
    started_at = perf_counter()
    response = predict_esi_for_intake(intake)
    response.latency_ms = max(0, round((perf_counter() - started_at) * 1000))
    response.assessment_id = assessment.id
    repositories.create_prediction(db, assessment.id, response)
    return response
