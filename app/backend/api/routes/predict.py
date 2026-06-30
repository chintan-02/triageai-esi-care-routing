from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.services.prediction_service import validate_prediction_contract

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=ESIPredictionResponse)
def predict_esi(
    intake: PatientIntakeRequest,
    db: Session = Depends(get_db),
) -> ESIPredictionResponse:
    assessment = repositories.create_assessment(db, intake)
    response = validate_prediction_contract(intake)
    response.assessment_id = assessment.id
    repositories.create_prediction(db, assessment.id, response)
    return response
